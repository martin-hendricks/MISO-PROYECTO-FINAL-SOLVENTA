import { inject, Injectable } from '@angular/core';
import { GOOGLE_MAPS_API_KEY } from './google-maps-key';

export type EstadoMapa = 'disponible' | 'no-disponible';

type VentanaMapas = Window & { gm_authFailure?: () => void };

/**
 * Loads the Maps JavaScript API the first time a provider map is shown.
 * An empty key, a script error or `gm_authFailure` leaves the map unavailable
 * so the caller can keep the ordered list.
 */
@Injectable({ providedIn: 'root' })
export class GoogleMapsLoaderService {
  private readonly apiKey = inject(GOOGLE_MAPS_API_KEY);
  private valor: EstadoMapa = 'no-disponible';
  private carga: Promise<EstadoMapa> | null = null;

  estado(): EstadoMapa {
    return this.valor;
  }

  cargar(): Promise<EstadoMapa> {
    if (!this.apiKey.trim()) {
      this.valor = 'no-disponible';
      return Promise.resolve(this.valor);
    }
    if (this.carga) {
      return this.carga;
    }
    this.carga = new Promise((resolve) => {
      const marcar = (estado: EstadoMapa) => {
        this.valor = estado;
        resolve(estado);
      };
      (window as VentanaMapas).gm_authFailure = () => marcar('no-disponible');
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(this.apiKey)}&v=weekly`;
      script.onload = () => marcar('disponible');
      script.onerror = () => marcar('no-disponible');
      document.head.appendChild(script);
    });
    return this.carga;
  }
}
