import { Billetera, Movimiento } from './billetera.gateway';

export const ASISTIDO: Movimiento = {
  id: '7b0c0000-0000-4000-8000-000000000001',
  siniestroId: 'SIN-1988',
  tipo: 'asistido',
  ramo: 'Protección de dispositivo',
  resumen: 'hurto',
  poliza: 'POL-88219-CO',
  monto: 890000,
  moneda: 'COP',
  comprobante: 'CMP-3F9A0C12DE',
  depositadoEn: '2026-07-11T15:20:00+00:00',
};

export const AUTOMATICO: Movimiento = {
  id: 'a51e0000-0000-4000-8000-000000000002',
  siniestroId: 'SIN-1002',
  tipo: 'pago_automatico',
  ramo: 'Clima y vuelos',
  resumen: 'retraso de vuelo',
  poliza: 'POL-11002-CO',
  monto: 180000,
  moneda: 'COP',
  comprobante: 'CMP-0A77B2C4F1',
  depositadoEn: '2026-07-02T09:05:00+00:00',
};

export const BILLETERA: Billetera = {
  moneda: 'COP',
  totalRecibido: 1070000,
  movimientos: [ASISTIDO, AUTOMATICO],
};
