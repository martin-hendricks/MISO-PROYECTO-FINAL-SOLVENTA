import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { GoogleMap, MapMarker } from '@angular/google-maps';
import { TranslatePipe } from '@ngx-translate/core';
import {
  COLOR_SINIESTRO,
  iconoPin,
  TipoPrestador,
  TIPOS_PRESTADOR,
} from '../tipo-prestador';

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

/** Google map for the customer list and the back-office pin. Renders nothing when unavailable. */
@Component({
  selector: 'sv-mapa-prestadores',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [GoogleMap, MapMarker, TranslatePipe],
  templateUrl: './mapa-prestadores.component.html',
  styleUrl: './mapa-prestadores.component.css',
})
export class MapaPrestadoresComponent {
  readonly disponible = input(false);
  readonly prestadores = input<readonly PinPrestador[]>([]);
  readonly centro = input<Punto>({ lat: 4.6097, lng: -74.0817 });
  readonly posicion = input<Punto | null>(null);
  readonly siniestro = input<Punto | null>(null);
  readonly etiquetaSiniestro = input('');
  readonly arrastrable = input(false);
  readonly pin = input<Punto | null>(null);
  readonly elegir = output<string>();
  readonly mover = output<Punto>();
  readonly fallo = output<void>();

  protected readonly tipos = TIPOS_PRESTADOR;
  protected readonly colorSiniestro = COLOR_SINIESTRO;

  protected icono(tipo: TipoPrestador): object {
    return iconoPin(tipo);
  }

  protected color(tipo: TipoPrestador): string {
    return iconoPin(tipo).fillColor;
  }

  protected soltar(evento: Arrastre): void {
    const punto = evento.latLng;
    if (!punto) {
      return;
    }
    this.mover.emit({ lat: punto.lat(), lng: punto.lng() });
  }
}
