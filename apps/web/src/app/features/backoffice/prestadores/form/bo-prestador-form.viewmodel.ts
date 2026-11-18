import { HttpErrorResponse } from '@angular/common/http';
import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { TipoPrestador } from '../../../prestadores/tipo-prestador';
import {
  PrestadorEntrada,
  PrestadorOperador,
} from '../bo-prestadores.gateway';

export type CodigoPrestador =
  | 'prestador_sin_ramo'
  | 'ramo_desconocido'
  | 'coordenada_fuera_de_rango';

export function codigoPrestador(error: unknown): CodigoPrestador | null {
  if (!(error instanceof HttpErrorResponse) || error.status !== 422) {
    return null;
  }
  const detail = (error.error as { detail?: string } | null)?.detail;
  if (
    detail === 'prestador_sin_ramo' ||
    detail === 'ramo_desconocido' ||
    detail === 'coordenada_fuera_de_rango'
  ) {
    return detail;
  }
  return null;
}

export interface PuertosFormulario {
  obtener: (id: string) => Observable<PrestadorOperador | null>;
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
  readonly ciudad = signal('');
  readonly ramos = signal<string[]>([]);
  readonly lat = signal<number | null>(null);
  readonly lng = signal<number | null>(null);
  readonly intento = signal(false);
  readonly errorCodigo = signal<string | null>(null);
  readonly guardado = signal(false);

  readonly errorRamo = computed(() => this.intento() && this.ramos().length === 0);

  constructor(
    private readonly puertos: PuertosFormulario,
    readonly id: string | null,
  ) {}

  cargar(): void {
    if (!this.id) {
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
        this.status.set('ready');
      },
      error: () => this.status.set('error'),
    });
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
