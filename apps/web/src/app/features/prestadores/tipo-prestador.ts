import type { Locale } from '../../core/i18n/locale.service';

export const TIPOS_PRESTADOR = [
  'servicio-tecnico',
  'taller-motos',
  'ips-urgencias',
  'grua',
  'asistencia-viajero',
  'punto-aeropuerto',
  'ips-examenes',
  'funeraria',
  'centro-atencion',
] as const;

export type TipoPrestador = (typeof TIPOS_PRESTADOR)[number];

export const RAMOS_PRESTADOR = [
  'proteccion-dispositivo',
  'soat-motocicleta',
  'microseguro-de-vida',
  'clima-y-vuelos',
  'vida-hipotecario',
  'pagos',
  'viaje',
  'vida-crediticia',
] as const;

export type RamoPrestador = (typeof RAMOS_PRESTADOR)[number];

export const PAISES = ['CO', 'MX', 'CL', 'PE'] as const;

export type Pais = (typeof PAISES)[number];

/** The country of the map and the catalog follows the app language. */
export const PAIS_POR_LOCALE: Record<Locale, Pais> = {
  'es-CO': 'CO',
  'es-MX': 'MX',
  'es-CL': 'CL',
  'es-PE': 'PE',
};

/** One color per type so the legend and the pins name the same thing. */
export const COLOR_PIN: Record<TipoPrestador, string> = {
  'servicio-tecnico': '#1565c0',
  'taller-motos': '#ef6c00',
  'ips-urgencias': '#c62828',
  grua: '#6a1b9a',
  'asistencia-viajero': '#00838f',
  'punto-aeropuerto': '#283593',
  'ips-examenes': '#ad1457',
  funeraria: '#455a64',
  'centro-atencion': '#2e7d32',
};

export const COLOR_SINIESTRO = '#005050';

export function formatoKm(km: number): string {
  return km.toFixed(1).replace('.', ',');
}

export function enlaceComoLlegar(punto: { lat: number; lng: number }): string {
  return `https://www.google.com/maps/dir/?api=1&destination=${punto.lat},${punto.lng}`;
}

export function enlaceLlamada(telefono: string): string {
  return `tel:${telefono.replace(/[^\d+]/g, '')}`;
}

/** Circle symbol. `path: 0` is `google.maps.SymbolPath.CIRCLE` without touching `google`. */
export function iconoPin(
  tipo: TipoPrestador,
  elegido = false,
): {
  path: number;
  fillColor: string;
  fillOpacity: number;
  strokeColor: string;
  strokeWeight: number;
  scale: number;
} {
  return {
    path: 0,
    fillColor: COLOR_PIN[tipo],
    fillOpacity: 1,
    strokeColor: '#181c1c',
    strokeWeight: elegido ? 2 : 1,
    scale: elegido ? 13 : 9,
  };
}
