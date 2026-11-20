import { HttpErrorResponse } from '@angular/common/http';
import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { ObjetivoCamara } from '../../../prestadores/mapa-prestadores/camara';
import { CiudadMapa } from '../../../prestadores/prestadores.gateway';
import { Pais, TipoPrestador } from '../../../prestadores/tipo-prestador';
import {
  PrestadorEntrada,
  PrestadorOperador,
} from '../bo-prestadores.gateway';

const CODIGOS = [
  'prestador_sin_ramo',
  'ramo_desconocido',
  'coordenada_fuera_de_rango',
  'ciudad_desconocida',
  'pais_desconocido',
] as const;

export type CodigoPrestador = (typeof CODIGOS)[number];

export function codigoPrestador(error: unknown): CodigoPrestador | null {
  if (!(error instanceof HttpErrorResponse) || error.status !== 422) {
    return null;
  }
  const codigo = (error.error as { codigo?: string } | null)?.codigo;
  return CODIGOS.find((conocido) => conocido === codigo) ?? null;
}

export interface PuertosFormulario {
  obtener: (id: string) => Observable<PrestadorOperador | null>;
  ciudades: (pais: Pais) => Observable<CiudadMapa[]>;
  guardar: (entrada: PrestadorEntrada, id: string | null) => Observable<PrestadorOperador>;
}

export class BoPrestadorFormViewModel {
  readonly status = signal<'loading' | 'ready' | 'saving' | 'error' | 'not-found'>('ready');
  readonly nombre = signal('');
  readonly barrio = signal('');
  readonly tipo = signal<TipoPrestador | ''>('');
  readonly telefono = signal('');
  readonly direccion = signal('');
  readonly horario = signal('');
  readonly pais = signal<Pais>('CO');
  readonly ciudades = signal<CiudadMapa[]>([]);
  readonly ciudad = signal('');
  readonly objetivo = signal<ObjetivoCamara | null>(null);
  readonly ramos = signal<string[]>([]);
  readonly lat = signal<number | null>(null);
  readonly lng = signal<number | null>(null);
  readonly intento = signal(false);
  readonly errorCodigo = signal<string | null>(null);
  readonly guardado = signal(false);

  readonly errorRamo = computed(() => this.intento() && this.ramos().length === 0);

  /** Without coordinates yet, the pin waits at the first city of the country. */
  readonly pin = computed(() => {
    const lat = this.lat();
    const lng = this.lng();
    if (lat !== null && lng !== null) {
      return { lat, lng };
    }
    const primera = this.ciudades()[0];
    return primera ? { lat: primera.lat, lng: primera.lng } : null;
  });

  private ticketCiudades = 0;

  constructor(
    private readonly puertos: PuertosFormulario,
    readonly id: string | null,
    pais: Pais,
  ) {
    this.pais.set(pais);
  }

  cargar(): void {
    if (!this.id) {
      this.cargarCiudades();
      this.status.set('ready');
      return;
    }
    this.status.set('loading');
    this.puertos.obtener(this.id).subscribe({
      next: (fila) => {
        if (!fila) {
          this.status.set('not-found');
          return;
        }
        this.volcar(fila);
        this.cargarCiudades();
        this.status.set('ready');
      },
      error: () => this.status.set('error'),
    });
  }

  elegirPais(pais: Pais): void {
    this.pais.set(pais);
    this.ciudad.set('');
    this.cargarCiudades();
  }

  elegirCiudad(nombre: string): void {
    this.ciudad.set(nombre);
    const ciudad = this.ciudades().find((opcion) => opcion.nombre === nombre);
    if (!ciudad) {
      return;
    }
    this.fijarPin(ciudad.lat, ciudad.lng);
    this.objetivo.set({ lat: ciudad.lat, lng: ciudad.lng, zoom: ciudad.zoom });
  }

  /** Called once the map shows, so saving without dragging keeps the visible pin. */
  anclarPin(): void {
    const pin = this.pin();
    if (pin && this.lat() === null) {
      this.fijarPin(pin.lat, pin.lng);
    }
  }

  alternarRamo(ramo: string): void {
    this.ramos.update((actual) =>
      actual.includes(ramo) ? actual.filter((item) => item !== ramo) : [...actual, ramo],
    );
  }

  fijarPin(lat: number, lng: number): void {
    this.lat.set(lat);
    this.lng.set(lng);
  }

  fijarLat(valor: string): void {
    this.lat.set(numero(valor));
  }

  fijarLng(valor: string): void {
    this.lng.set(numero(valor));
  }

  guardar(): void {
    this.intento.set(true);
    this.errorCodigo.set(null);
    if (!this.valido()) {
      return;
    }
    this.status.set('saving');
    this.puertos.guardar(this.entrada(), this.id).subscribe({
      next: () => {
        this.status.set('ready');
        this.guardado.set(true);
      },
      error: (error: unknown) => {
        this.status.set('error');
        this.errorCodigo.set(codigoPrestador(error) ?? 'generico');
      },
    });
  }

  private cargarCiudades(): void {
    const ticket = ++this.ticketCiudades;
    this.ciudades.set([]);
    this.puertos.ciudades(this.pais()).subscribe({
      next: (ciudades) => {
        if (ticket === this.ticketCiudades) {
          this.ciudades.set(ciudades);
        }
      },
      error: () => undefined,
    });
  }

  private valido(): boolean {
    return Boolean(
      this.nombre().trim() &&
        this.barrio().trim() &&
        this.tipo() &&
        this.telefono().trim() &&
        this.direccion().trim() &&
        this.horario().trim() &&
        this.ciudad().trim() &&
        this.ramos().length &&
        this.lat() !== null &&
        this.lng() !== null,
    );
  }

  private entrada(): PrestadorEntrada {
    return {
      nombre: this.nombre().trim(),
      tipo: this.tipo() as TipoPrestador,
      ramos: [...this.ramos()],
      direccion: this.direccion().trim(),
      pais: this.pais(),
      ciudad: this.ciudad().trim(),
      barrio: this.barrio().trim(),
      lat: this.lat()!,
      lng: this.lng()!,
      telefono: this.telefono().trim(),
      horario: this.horario().trim(),
    };
  }

  private volcar(fila: PrestadorOperador): void {
    this.nombre.set(fila.nombre);
    this.barrio.set(fila.barrio);
    this.tipo.set(fila.tipo);
    this.telefono.set(fila.telefono);
    this.direccion.set(fila.direccion);
    this.horario.set(fila.horario);
    this.pais.set(fila.pais);
    this.ciudad.set(fila.ciudad);
    this.ramos.set([...fila.ramos]);
    this.lat.set(fila.lat);
    this.lng.set(fila.lng);
  }
}

function numero(valor: string): number | null {
  const texto = valor.trim();
  if (!texto) {
    return null;
  }
  const n = Number(texto);
  return Number.isNaN(n) ? null : n;
}
