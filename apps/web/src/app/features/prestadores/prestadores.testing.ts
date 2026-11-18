import {
  AreaVisible,
  BusquedaPrestadores,
  BusquedaSiniestro,
  CiudadMapa,
  Prestador,
} from './prestadores.gateway';

export const PRESTADOR: Prestador = {
  id: 'PRE-BOG-06',
  nombre: 'Taller Moto Chapinero',
  tipo: 'taller-motos',
  ramos: ['soat-motocicleta'],
  direccion: 'Cra 13 #45-18',
  ciudad: 'Bogotá',
  pais: 'CO',
  barrio: 'Chapinero',
  lat: 4.6355,
  lng: -74.0655,
  telefono: '601 555 0112',
  horario: 'Lun–Sáb 7:00–19:00',
  distanciaKm: 0.9,
};

export const IPS: Prestador = {
  ...PRESTADOR,
  id: 'PRE-BOG-01',
  nombre: 'IPS Urgencias Chapinero',
  tipo: 'ips-urgencias',
  ramos: ['microseguro-de-vida', 'viaje'],
  lat: 4.6482,
  lng: -74.0628,
  distanciaKm: 1.2,
};

export const BUSQUEDA: BusquedaPrestadores = {
  centro: { lat: 4.6432, lng: -74.0631, origen: 'posicion' },
  radioKm: 10,
  truncado: false,
  prestadores: [PRESTADOR],
};

export const BUSQUEDA_SINIESTRO: BusquedaSiniestro = {
  ...BUSQUEDA,
  centro: { lat: 4.626, lng: -74.15, origen: 'siniestro' },
  siniestro: { id: 'sin-1988', numero: 'SIN-1988', ramo: 'soat-motocicleta' },
  ramoFijo: 'soat-motocicleta',
  sinGeoetiqueta: false,
  prestadores: [{ ...PRESTADOR, distanciaKm: 0.8 }],
};

export const CIUDADES_CO: CiudadMapa[] = [
  { nombre: 'Bogotá', lat: 4.6097, lng: -74.0817, zoom: 12, prestadores: 30 },
  { nombre: 'Medellín', lat: 6.2442, lng: -75.5812, zoom: 13, prestadores: 20 },
  { nombre: 'Chía', lat: 4.8619, lng: -74.0597, zoom: 13, prestadores: 10 },
];

export const CIUDADES_MX: CiudadMapa[] = [
  { nombre: 'Ciudad de México', lat: 19.4326, lng: -99.1332, zoom: 11, prestadores: 5 },
  { nombre: 'Guadalajara', lat: 20.6597, lng: -103.3496, zoom: 13, prestadores: 4 },
  { nombre: 'Monterrey', lat: 25.6866, lng: -100.3161, zoom: 13, prestadores: 4 },
];

export const AREA_CHAPINERO: AreaVisible = { norte: 4.66, sur: 4.62, este: -74.05, oeste: -74.08 };

export const AREA_MEDELLIN: AreaVisible = { norte: 6.28, sur: 6.2, este: -75.54, oeste: -75.62 };
