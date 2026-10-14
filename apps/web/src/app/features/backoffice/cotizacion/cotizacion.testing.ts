import { Oferta } from './cotizacion.gateway';
import { CotizacionForm } from './cotizacion.viewmodel';

/** Same offer the `bff-web` stub answers. For specs only. */
export const OFERTA: Oferta = {
  cotizacionId: 'COT-1042',
  estado: 'oferta_vigente',
  prima: 89000,
  primaNeta: 72500,
  gastosExpedicion: 16500,
  moneda: 'COP',
  vigenciaMeses: 12,
  venceEn: '2026-10-01',
};

export const FORMULARIO: CotizacionForm = {
  nombre: 'Andrés Gómez Molina',
  documento: '1020334556',
  vigenciaMeses: 12,
  tipo: 'telefono',
  valorAsegurado: '1200000',
  marca: 'Samsung',
  modelo: 'Galaxy A54',
};
