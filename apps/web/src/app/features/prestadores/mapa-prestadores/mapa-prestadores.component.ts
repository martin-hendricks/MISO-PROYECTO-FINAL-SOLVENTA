import {
  afterRenderEffect,
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  ElementRef,
  inject,
  input,
  output,
  untracked,
  viewChild,
} from '@angular/core';
import { GoogleMap, MapMarker, MapMarkerClusterer } from '@angular/google-maps';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { ALGORITMO, apilarCoincidentes, registrarAgrupador, RenderizadorGrupos } from '../agrupar';
import { AreaVisible } from '../prestadores.gateway';
import {
  COLOR_SINIESTRO,
  iconoPin,
  TipoPrestador,
  TIPOS_PRESTADOR,
} from '../tipo-prestador';
import {
  areaDeLimites,
  dentroDelArea,
  desplazamientoTarjeta,
  ObjetivoCamara,
} from './camara';

export interface Punto {
  lat: number;
  lng: number;
}

export interface PinPrestador {
  id: string;
  nombre: string;
  tipo: TipoPrestador;
  lat: number;
  lng: number;
}

interface Arrastre {
  latLng?: { lat: () => number; lng: () => number } | null;
}

const Z_ELEGIDO = 2_000_000;
const Z_PROPIO = 3_000_000;

/** Google map for the customer map and the back-office pin. Renders nothing when unavailable. */
@Component({
  selector: 'sv-mapa-prestadores',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [GoogleMap, MapMarker, MapMarkerClusterer, TranslatePipe],
  templateUrl: './mapa-prestadores.component.html',
  styleUrl: './mapa-prestadores.component.css',
})
export class MapaPrestadoresComponent {
  private readonly translate = inject(TranslateService);

  readonly disponible = input(false);
  readonly prestadores = input<readonly PinPrestador[]>([]);
  readonly centro = input<Punto | null>(null);
  readonly zoom = input(13);
  readonly objetivo = input<ObjetivoCamara | null>(null);
  readonly seleccion = input<readonly string[]>([]);
  readonly posicion = input<Punto | null>(null);
  readonly siniestro = input<Punto | null>(null);
  readonly etiquetaSiniestro = input('');
  readonly arrastrable = input(false);
  readonly pin = input<Punto | null>(null);
  readonly elegir = output<string[]>();
  readonly mover = output<Punto>();
  readonly moverCamara = output<AreaVisible>();
  readonly arrastrar = output<void>();
  readonly tocarMapa = output<void>();
  readonly fallo = output<void>();

  private readonly mapa = viewChild(GoogleMap);
  private readonly lienzoMapa = viewChild<ElementRef<HTMLElement>>('lienzoMapa');
  private readonly capaTarjeta = viewChild<ElementRef<HTMLElement>>('capaTarjeta');

  protected readonly tipos = TIPOS_PRESTADOR;
  protected readonly colorSiniestro = COLOR_SINIESTRO;
  protected readonly algoritmo = ALGORITMO;
  protected readonly renderizador = new RenderizadorGrupos((n) =>
    this.translate.instant('prestadores.grupo', { n }),
  );
  protected readonly zPropio = Z_PROPIO;

  protected readonly grupos = computed(() => apilarCoincidentes(this.prestadores()));

  /** Read once: later camera moves go through `panTo`/`setZoom` so the map keeps the user's view. */
  protected readonly opciones = computed<google.maps.MapOptions>(() => {
    const objetivo = untracked(this.objetivo);
    return {
      gestureHandling: 'greedy',
      minZoom: 5,
      maxZoom: 18,
      rotateControl: false,
      tilt: 0,
      keyboardShortcuts: true,
      streetViewControl: false,
      mapTypeControl: false,
      fullscreenControl: false,
      clickableIcons: false,
      zoomControlOptions: { position: google.maps.ControlPosition.RIGHT_TOP },
      ...(objetivo ? { center: { lat: objetivo.lat, lng: objetivo.lng }, zoom: objetivo.zoom } : {}),
    };
  });

  constructor() {
    registrarAgrupador();

    effect(() => {
      const objetivo = this.objetivo();
      const mapa = this.mapa();
      if (!objetivo || !mapa?.googleMap) {
        return;
      }
      mapa.panTo({ lat: objetivo.lat, lng: objetivo.lng });
      mapa.googleMap.setZoom(objetivo.zoom);
    });

    afterRenderEffect(() => {
      const [primero] = this.seleccion();
      const elegido = this.prestadores().find((prestador) => prestador.id === primero);
      const mapa = this.mapa();
      const limites = mapa?.getBounds();
      const lienzo = this.lienzoMapa()?.nativeElement;
      const tarjeta = this.capaTarjeta()?.nativeElement;
      if (!elegido || !mapa || !limites || !lienzo || !tarjeta) {
        return;
      }
      const area = areaDeLimites(limites);
      if (!dentroDelArea(area, elegido)) {
        return;
      }
      const desplazar = desplazamientoTarjeta(
        area,
        elegido.lat,
        lienzo.clientHeight,
        tarjeta.offsetHeight,
      );
      if (desplazar > 0) {
        mapa.panBy(0, desplazar);
      }
    });
  }

  protected alDetenerse(): void {
    const limites = this.mapa()?.getBounds();
    if (limites) {
      this.moverCamara.emit(areaDeLimites(limites));
    }
  }

  protected idsDe(prestadores: readonly PinPrestador[]): string[] {
    return prestadores.map((prestador) => prestador.id);
  }

  protected elegido(ids: readonly string[]): boolean {
    const seleccion = this.seleccion();
    return ids.some((id) => seleccion.includes(id));
  }

  protected icono(tipo: TipoPrestador, elegido = false): google.maps.Symbol {
    return iconoPin(tipo, elegido) as google.maps.Symbol;
  }

  protected color(tipo: TipoPrestador): string {
    return iconoPin(tipo).fillColor;
  }

  protected opcionesPin(elegido: boolean): google.maps.MarkerOptions {
    return elegido ? { zIndex: Z_ELEGIDO } : {};
  }

  protected soltar(evento: Arrastre): void {
    const punto = evento.latLng;
    if (!punto) {
      return;
    }
    this.mover.emit({ lat: punto.lat(), lng: punto.lng() });
  }
}
