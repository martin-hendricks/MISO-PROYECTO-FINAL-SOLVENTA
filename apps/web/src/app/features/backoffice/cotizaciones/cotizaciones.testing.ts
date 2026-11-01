import { CotizacionesPagina, CotizacionPendiente } from './cotizaciones.gateway';

/** Pending quotes as `bff-web` answers them. For specs only. */
export const VIGENTE: CotizacionPendiente = {
  cotizacionId: 'COT-1',
  ofertaId: 'OF-1',
  ramo: 'autos',
  estado: 'cotizada',
  prima: 42300,
  moneda: 'COP',
  creadaEn: '2026-10-20T10:00:00Z',
  venceEn: '2026-11-19T10:00:00Z',
  vencida: false,
  clienteRef: 'CLI-18',
};

export const VENCIDA: CotizacionPendiente = {
  ...VIGENTE,
  cotizacionId: 'COT-2',
  ofertaId: 'OF-2',
  estado: 'aceptada',
  venceEn: '2026-09-01T10:00:00Z',
  vencida: true,
  clienteRef: 'CLI-19',
};

export function pagina(
  items: CotizacionPendiente[],
  extra: Partial<CotizacionesPagina> = {},
): CotizacionesPagina {
  return { items, pagina: 1, tamano: 20, hayMas: false, avisos: [], ...extra };
}
