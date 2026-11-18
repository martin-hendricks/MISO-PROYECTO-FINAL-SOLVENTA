import { BusquedaPrestadores, BusquedaSiniestro, Prestador } from './prestadores.gateway';

export const PRESTADOR: Prestador = {
  id: 'PRE-BOG-06',
  nombre: 'Taller Moto Chapinero',
  tipo: 'taller-motos',
  ramos: ['soat-motocicleta'],
  direccion: 'Cra 13 #45-18',
  ciudad: 'Bogotá',
  barrio: 'Chapinero',
  lat: 4.6355,
  lng: -74.0655,
  telefono: '601 555 0112',
  horario: 'Lun–Sáb 7:00–19:00',
  distanciaKm: 0.9,
};

export const BUSQUEDA: BusquedaPrestadores = {
  centro: { lat: 4.6432, lng: -74.0631, origen: 'posicion' },
  radioKm: 10,
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
