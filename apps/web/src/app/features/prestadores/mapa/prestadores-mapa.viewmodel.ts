import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import type { Locale } from '../../../core/i18n/locale.service';
import { GeolocationPort, Posicion } from '../geolocation-port';
import { areaConSuperficie, dentroDelArea, ObjetivoCamara, ZOOM_CERCA } from '../mapa-prestadores/camara';
import {
  AreaVisible,
  BusquedaPrestadores,
  BusquedaSiniestro,
  CiudadMapa,
  ConsultaPrestadores,
  Prestador,
} from '../prestadores.gateway';
import {
  enlaceComoLlegar,
  enlaceLlamada,
  formatoKm,
  Pais,
  PAIS_POR_LOCALE,
} from '../tipo-prestador';

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
  ciudades: (pais: Pais) => Observable<CiudadMapa[]>;
  porSiniestro: (id: string, area?: AreaVisible) => Observable<BusquedaSiniestro | null>;
}

export const ESPERA_CAMARA_MS = 300;

export function esBloqueoUbicacion(error: unknown): boolean {
  const code =
    typeof error === 'object' && error !== null && 'code' in error
      ? (error as { code: unknown }).code
      : null;
  return code === 1 || code === 2 || code === 3;
}

/**
 * With the map, results follow the visible area 300 ms after the camera stops.
 * Without it, the list uses the 005 queries (radius around the person or a city).
 */
export class PrestadoresMapaViewModel {
  readonly status = signal<EstadoPrestadores>('loading');
  readonly modo = signal<ModoPrestadores>('nearMe');
  readonly mapa = signal<EstadoMapa>('no-disponible');
  readonly ramo = signal<string | null>(null);
  readonly prestadores = signal<Prestador[]>([]);
  readonly truncado = signal(false);
  readonly centro = signal<{ lat: number; lng: number } | null>(null);
  readonly posicion = signal<Posicion | null>(null);
  readonly siniestro = signal<{ id: string; numero: string; ramo: string | null } | null>(null);
  readonly abiertoId = signal<string | null>(null);
  readonly ciudades = signal<CiudadMapa[]>([]);
  readonly ciudadMarcada = signal<string | null>(null);
  readonly area = signal<AreaVisible | null>(null);
  readonly objetivoCamara = signal<ObjetivoCamara | null>(null);
  readonly seleccion = signal<Prestador[]>([]);
  private readonly ciudadesLeidas = signal(false);

  readonly pais = computed<Pais>(() => PAIS_POR_LOCALE[this.locale()]);
  readonly ramoBloqueado = computed(() => this.modo() === 'claim');
  readonly diceCercaDeTi = computed(() => this.modo() === 'nearMe');
  readonly muestraDistancias = computed(() => this.modo() === 'nearMe' || this.modo() === 'claim');
  readonly referenciaDistancia = computed<'evento' | 'posicion' | null>(() => {
    if (!this.muestraDistancias()) {
      return null;
    }
    return this.modo() === 'claim' ? 'evento' : 'posicion';
  });
  readonly muestraChips = computed(() => this.modo() !== 'claim' && this.ciudades().length > 0);
  readonly paisVacio = computed(
    () => this.modo() !== 'claim' && this.ciudadesLeidas() && this.ciudades().length === 0,
  );
  readonly miUbicacionVisible = computed(() => this.posicion() !== null);

  private ticket = 0;
  private espera: ReturnType<typeof setTimeout> | undefined;

  constructor(
    private readonly puertos: PuertosPrestadores,
    private readonly geo: GeolocationPort,
    readonly claimId: string | null,
    private readonly locale: () => Locale,
  ) {}

  /** Losing the map after a camera target reloads with the list queries. */
  fijarMapa(estado: EstadoMapa): void {
    const perdido = this.mapa() === 'disponible' && estado === 'no-disponible';
    this.mapa.set(estado);
    if (perdido && this.objetivoCamara()) {
      this.refrescar();
    }
  }

  cargar(): void {
    if (this.claimId) {
      this.cargarSiniestro();
      return;
    }
    const ticket = ++this.ticket;
    this.status.set('loading');
    this.puertos.ciudades(this.pais()).subscribe({
      next: (ciudades) => {
        if (ticket !== this.ticket) {
          return;
        }
        this.ciudades.set(ciudades);
        this.ciudadesLeidas.set(true);
        this.pedirUbicacion();
      },
      error: () => {
        if (ticket === this.ticket) {
          this.status.set('error');
        }
      },
    });
  }

  /** Retries the last area when there is one; otherwise starts over. */
  reintentar(): void {
    if (this.area()) {
      this.refrescar();
      return;
    }
    this.cargar();
  }

  usarUbicacion(): void {
    this.pedirUbicacion();
  }

  usarMiUbicacion(): void {
    const posicion = this.posicion();
    if (!posicion) {
      return;
    }
    this.ciudadMarcada.set(null);
    this.apuntar({ ...posicion, zoom: ZOOM_CERCA });
  }

  alMoverCamara(area: AreaVisible): void {
    if (!areaConSuperficie(area)) {
      return;
    }
    this.area.set(area);
    clearTimeout(this.espera);
    this.espera = setTimeout(() => this.refrescar(), ESPERA_CAMARA_MS);
  }

  alArrastrar(): void {
    this.ciudadMarcada.set(null);
  }

  seleccionarRamo(ramo: string | null): void {
    if (this.ramoBloqueado()) {
      return;
    }
    this.ramo.set(ramo);
    this.refrescar();
  }

  elegirCiudad(ciudad: CiudadMapa): void {
    this.ciudadMarcada.set(ciudad.nombre);
    this.apuntar({ lat: ciudad.lat, lng: ciudad.lng, zoom: ciudad.zoom });
  }

  seleccionar(ids: readonly string[]): void {
    this.seleccion.set(this.prestadores().filter((prestador) => ids.includes(prestador.id)));
  }

  /** On the map the row opens the card; in the list fallback it expands the row. */
  seleccionarDesdeLista(prestador: Prestador): void {
    if (this.mapa() !== 'disponible') {
      this.abrir(prestador.id);
      return;
    }
    this.seleccion.set([prestador]);
    this.objetivoCamara.set({ lat: prestador.lat, lng: prestador.lng, zoom: ZOOM_CERCA });
  }

  cerrarTarjeta(): void {
    this.seleccion.set([]);
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
    return enlaceComoLlegar(prestador);
  }

  llamar(prestador: Prestador): string {
    return enlaceLlamada(prestador.telefono);
  }

  private pedirUbicacion(): void {
    const ticket = ++this.ticket;
    this.status.set('loading');
    void this.geo.actual().then(
      (posicion) => {
        if (ticket !== this.ticket) {
          return;
        }
        this.modo.set('nearMe');
        this.posicion.set(posicion);
        this.ciudadMarcada.set(null);
        this.apuntar({ ...posicion, zoom: ZOOM_CERCA });
      },
      (error: unknown) => {
        if (ticket !== this.ticket) {
          return;
        }
        if (!esBloqueoUbicacion(error)) {
          this.status.set('error');
          return;
        }
        this.modo.set('chooseCity');
        this.posicion.set(null);
        const primera = this.ciudades()[0];
        if (!primera) {
          this.prestadores.set([]);
          this.status.set('empty');
          return;
        }
        this.elegirCiudad(primera);
      },
    );
  }

  /** The map reports the new area when it stops; without it the list loads right away. */
  private apuntar(objetivo: ObjetivoCamara): void {
    this.objetivoCamara.set(objetivo);
    if (this.mapa() !== 'disponible') {
      this.refrescar();
    }
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
        if (resultado.sinGeoetiqueta || !resultado.centro) {
          this.prestadores.set([]);
          this.status.set('sin-geo');
          return;
        }
        const { lat, lng } = resultado.centro;
        this.centro.set({ lat, lng });
        this.objetivoCamara.set({ lat, lng, zoom: ZOOM_CERCA });
        this.aplicar(resultado);
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
    const lectura: Observable<BusquedaPrestadores | null> =
      this.modo() === 'claim'
        ? this.puertos.porSiniestro(this.claimId!, this.area() ?? undefined)
        : this.puertos.cercanos(this.consulta());
    lectura.subscribe({
      next: (resultado) => {
        if (ticket !== this.ticket) {
          return;
        }
        if (!resultado) {
          this.status.set('not-found');
          return;
        }
        this.aplicar(resultado);
      },
      error: () => {
        if (ticket === this.ticket) {
          this.status.set('error');
        }
      },
    });
  }

  private consulta(): ConsultaPrestadores {
    const base = { ramo: this.ramo(), pais: this.pais() };
    const origen = this.modo() === 'nearMe' ? this.posicion() : null;
    const area = this.area();
    if (area) {
      return origen ? { ...base, area, origen } : { ...base, area };
    }
    const ciudad = this.ciudadMarcada();
    if (origen && !ciudad) {
      return { ...base, origen, radioKm: 10 };
    }
    return { ...base, ciudad: ciudad! };
  }

  private aplicar(resultado: BusquedaPrestadores): void {
    this.prestadores.set(resultado.prestadores);
    this.truncado.set(resultado.truncado);
    this.conservarSeleccion(resultado.prestadores);
    this.status.set(resultado.prestadores.length ? 'ready' : 'empty');
  }

  /**
   * Panning keeps the card open: a chosen provider outside the new area stays
   * while it serves the ramo. Missing from an area that covers it, it closes.
   */
  private conservarSeleccion(prestadores: Prestador[]): void {
    const area = this.area();
    const ramo = this.ramo();
    this.seleccion.update((elegidos) =>
      elegidos.flatMap((elegido) => {
        const vigente = prestadores.find((prestador) => prestador.id === elegido.id);
        if (vigente) {
          return [vigente];
        }
        const fuera = area !== null && !dentroDelArea(area, elegido);
        return fuera && (ramo === null || elegido.ramos.includes(ramo)) ? [elegido] : [];
      }),
    );
  }
}
