import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { GeolocationPort, Posicion } from '../geolocation-port';
import {
  BusquedaPrestadores,
  BusquedaSiniestro,
  ConsultaPrestadores,
  Prestador,
} from '../prestadores.gateway';
import type { CiudadPrestador } from '../tipo-prestador';

export type ModoPrestadores = 'nearMe' | 'chooseCity' | 'claim';
export type EstadoPrestadores =
  | 'loading'
  | 'ready'
  | 'empty'
  | 'error'
  | 'not-found'
  | 'sin-geo';
export type EstadoMapa = 'disponible' | 'no-disponible';

export interface PuertosPrestadores {
  cercanos: (consulta: ConsultaPrestadores) => Observable<BusquedaPrestadores>;
  porSiniestro: (id: string) => Observable<BusquedaSiniestro | null>;
}

const CIUDAD_INICIAL: CiudadPrestador = 'Bogotá';

export function esBloqueoUbicacion(error: unknown): boolean {
  const code =
    typeof error === 'object' && error !== null && 'code' in error
      ? (error as { code: unknown }).code
      : null;
  return code === 1 || code === 2 || code === 3;
}

export function formatoKm(km: number): string {
  return km.toFixed(1).replace('.', ',');
}

export class PrestadoresMapaViewModel {
  readonly status = signal<EstadoPrestadores>('loading');
  readonly modo = signal<ModoPrestadores>('nearMe');
  readonly mapa = signal<EstadoMapa>('no-disponible');
  readonly ramo = signal<string | null>(null);
  readonly ciudad = signal<CiudadPrestador>(CIUDAD_INICIAL);
  readonly prestadores = signal<Prestador[]>([]);
  readonly radioKm = signal(10);
  readonly centro = signal<{ lat: number; lng: number } | null>(null);
  readonly posicion = signal<Posicion | null>(null);
  readonly siniestro = signal<{ id: string; numero: string; ramo: string | null } | null>(null);
  readonly abiertoId = signal<string | null>(null);

  readonly ramoBloqueado = computed(() => this.modo() === 'claim');
  readonly diceCercaDeTi = computed(() => this.modo() === 'nearMe');
  readonly muestraDistancias = computed(() => this.modo() === 'nearMe' || this.modo() === 'claim');
  readonly referenciaDistancia = computed<'evento' | 'posicion' | null>(() => {
    if (!this.muestraDistancias()) {
      return null;
    }
    return this.modo() === 'claim' ? 'evento' : 'posicion';
  });

  private ticket = 0;
  private coords: Posicion | null = null;

  constructor(
    private readonly puertos: PuertosPrestadores,
    private readonly geo: GeolocationPort,
    readonly claimId: string | null,
  ) {}

  /** The list stays. A missing map does not turn a failed read into an empty one. */
  fijarMapa(estado: EstadoMapa): void {
    this.mapa.set(estado);
  }

  cargar(): void {
    if (this.claimId) {
      this.cargarSiniestro();
      return;
    }
    this.pedirUbicacion();
  }

  usarUbicacion(): void {
    this.pedirUbicacion();
  }

  seleccionarRamo(ramo: string | null): void {
    if (this.ramoBloqueado()) {
      return;
    }
    this.ramo.set(ramo);
    this.refrescar();
  }

  elegirCiudad(ciudad: CiudadPrestador): void {
    this.modo.set('chooseCity');
    this.ciudad.set(ciudad);
    this.coords = null;
    this.posicion.set(null);
    this.refrescar();
  }

  abrir(id: string): void {
    this.abiertoId.set(this.abiertoId() === id ? null : id);
  }

  km(prestador: Prestador): string | null {
    if (!this.muestraDistancias() || prestador.distanciaKm === null) {
      return null;
    }
    return formatoKm(prestador.distanciaKm);
  }

  comoLlegar(prestador: Prestador): string {
    return `https://www.google.com/maps/dir/?api=1&destination=${prestador.lat},${prestador.lng}`;
  }

  private pedirUbicacion(): void {
    const ticket = ++this.ticket;
    this.status.set('loading');
    void this.geo.actual().then(
      (pos) => {
        if (ticket !== this.ticket) {
          return;
        }
        this.modo.set('nearMe');
        this.coords = pos;
        this.posicion.set(pos);
        this.buscar(ticket);
      },
      (error: unknown) => {
        if (ticket !== this.ticket) {
          return;
        }
        if (esBloqueoUbicacion(error)) {
          this.modo.set('chooseCity');
          this.ciudad.set(CIUDAD_INICIAL);
          this.coords = null;
          this.posicion.set(null);
          this.buscar(ticket);
          return;
        }
        this.prestadores.set([]);
        this.status.set('error');
      },
    );
  }

  private cargarSiniestro(): void {
    const ticket = ++this.ticket;
    this.modo.set('claim');
    this.status.set('loading');
    this.puertos.porSiniestro(this.claimId!).subscribe({
      next: (resultado) => {
        if (ticket !== this.ticket) {
          return;
        }
        if (!resultado) {
          this.prestadores.set([]);
          this.status.set('not-found');
          return;
        }
        this.siniestro.set(resultado.siniestro);
        this.ramo.set(resultado.ramoFijo);
        this.radioKm.set(resultado.radioKm);
        this.centro.set(resultado.centro);
        if (resultado.sinGeoetiqueta || !resultado.centro) {
          this.prestadores.set([]);
          this.status.set('sin-geo');
          return;
        }
        this.prestadores.set(resultado.prestadores);
        this.status.set(resultado.prestadores.length ? 'ready' : 'empty');
      },
      error: () => {
        if (ticket !== this.ticket) {
          return;
        }
        this.prestadores.set([]);
        this.status.set('error');
      },
    });
  }

  private refrescar(): void {
    const ticket = ++this.ticket;
    this.status.set('loading');
    this.buscar(ticket);
  }

  private buscar(ticket: number): void {
    const coords = this.modo() === 'nearMe' ? this.coords : null;
    const consulta: ConsultaPrestadores = coords
      ? { lat: coords.lat, lng: coords.lng, ramo: this.ramo(), radioKm: 10 }
      : { ciudad: this.ciudad(), ramo: this.ramo() };
    this.puertos.cercanos(consulta).subscribe({
      next: (resultado) => {
        if (ticket !== this.ticket) {
          return;
        }
        this.radioKm.set(resultado.radioKm);
        this.centro.set(resultado.centro);
        this.prestadores.set(resultado.prestadores);
        this.status.set(resultado.prestadores.length ? 'ready' : 'empty');
      },
      error: () => {
        if (ticket !== this.ticket) {
          return;
        }
        this.prestadores.set([]);
        this.status.set('error');
      },
    });
  }
}
