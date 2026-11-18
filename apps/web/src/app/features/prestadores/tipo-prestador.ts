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

export const CIUDADES_PRESTADOR = [
  { id: 'Bogotá', slug: 'bogota', lat: 4.6097, lng: -74.0817 },
  { id: 'Medellín', slug: 'medellin', lat: 6.2442, lng: -75.5812 },
  { id: 'Chía', slug: 'chia', lat: 4.8619, lng: -74.0597 },
] as const;

export type CiudadPrestador = (typeof CIUDADES_PRESTADOR)[number]['id'];

export const CENTRO_BOGOTA = { lat: 4.6097, lng: -74.0817 };

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

/** Circle symbol. `path: 0` is `google.maps.SymbolPath.CIRCLE` without touching `google`. */
export function iconoPin(tipo: TipoPrestador): {
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
    strokeWeight: 1,
    scale: 9,
  };
}
