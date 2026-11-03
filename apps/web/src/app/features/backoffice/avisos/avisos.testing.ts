import { AvisoFila, CasoAviso, Cola } from './avisos.gateway';

/** Contrato de bff-web (router_operador en routers/siniestros.py). Solo para specs. */
export const FILA: AvisoFila = {
  id: '11111111-1111-4111-8111-111111111111',
  siniestroId: 'SIN-2041',
  clienteId: '66666666-6666-4666-8666-666666666666',
  poliza: 'POL-88421',
  ramo: 'vida-crediticia',
  recibidoEn: '2026-11-02T10:00:00Z',
  estado: 'en_evaluacion',
  estadoCola: 'en_revision',
  resultado: null,
  requiereRevision: true,
};

export const COLA: Cola = {
  filtro: 'pendientes',
  conteos: { pendientes: 1, aprobados: 0, rechazados: 0, todos: 1 },
  avisos: [FILA],
};

export const COLA_VACIA: Cola = {
  filtro: 'pendientes',
  conteos: { pendientes: 0, aprobados: 0, rechazados: 0, todos: 0 },
  avisos: [],
};

export const CASO: CasoAviso = {
  ...FILA,
  fechaHecho: '2026-09-14',
  descripcion: 'Fallecimiento del asegurado',
  geo: { lat: '4.653300', lng: '-74.083600', precision_m: '12.00' },
  montoEstimado: 3200000,
  umbralAutomatico: 500000,
  bajoMonto: false,
  moneda: 'COP',
  clavePago: 'idem-111111111111',
  motivoRevision: 'La reserva supera el umbral de aprobación automática',
  evidencia: [
    {
      nombre: 'certificado.pdf',
      tipo: 'documento',
      contentType: 'application/pdf',
      url: 'https://s3/firmada',
    },
  ],
  decisiones: [
    {
      origen: 'motor',
      actor: 'motor-reglas-siniestros',
      resultado: 'revision',
      motivo: 'La reserva supera el umbral de aprobación automática',
      reglas: [],
      decidida_en: '2026-11-02T10:00:02Z',
    },
  ],
  historial: [
    { estado: 'recibido', fecha: '2026-11-02T10:00:00Z' },
    { estado: 'en_evaluacion', fecha: '2026-11-02T10:00:02Z' },
  ],
  pago: null,
  intentosPago: [],
};

/** Bajo monto retenido (p. ej. por el antifraude): el operador puede aprobar y pagar. */
export const CASO_BAJO_MONTO: CasoAviso = {
  ...CASO,
  ramo: 'proteccion-dispositivo',
  montoEstimado: 420000,
  bajoMonto: true,
  motivoRevision: 'Posible duplicado: la póliza tiene otro aviso reciente',
};
