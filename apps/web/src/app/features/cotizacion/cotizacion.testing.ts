import { HttpErrorResponse } from '@angular/common/http';
import { Oferta } from './cotizacion.gateway';

/** Answers shaped as bff-web's `/v1/{cliente,asesor}/cotizaciones`. For specs only. */
export const OFERTA_WIRE = {
  cotizacionId: 'COT-4471',
  ramo: 'SOAT motocicleta',
  estado: 'cotizada',
  prima: '128500.00',
  moneda: 'COP',
  venceEn: '2026-11-24T15:00:00Z',
};

export const OFERTA: Oferta = {
  ...OFERTA_WIRE,
  prima: 128500,
  primaNeta: undefined,
  expedicion: undefined,
};

/** Breakdown bff-web will add (pending on SOLV-165). */
export const OFERTA_DESGLOSE_WIRE = { ...OFERTA_WIRE, primaNeta: '120000', expedicion: '8500' };

export const FUERA_DE_RANGO = {
  codigo: 'dato_riesgo_fuera_de_rango',
  mensaje: "'cilindraje_cc' fuera de rango: 50 a 1800",
};

export const fueraDeRango = () => new HttpErrorResponse({ status: 422, error: FUERA_DE_RANGO });
