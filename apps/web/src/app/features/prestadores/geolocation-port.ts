import { InjectionToken } from '@angular/core';

export interface Posicion {
  lat: number;
  lng: number;
}

/** Browser location behind a port so the map view model can be tested without `navigator`. */
export interface GeolocationPort {
  actual(): Promise<Posicion>;
}

export const GEOLOCATION_PORT = new InjectionToken<GeolocationPort>('GEOLOCATION_PORT', {
  factory: () => ({
    actual: () =>
      new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
          reject({ code: 1 });
          return;
        }
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
          (error) => reject(error),
          { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 },
        );
      }),
  }),
});
