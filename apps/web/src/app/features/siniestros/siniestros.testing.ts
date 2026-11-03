import { SiniestroDetalle, SiniestroResumen } from './siniestros.gateway';

/** Contrato de bff-web (routers/siniestros.py). Solo para specs. */
export const SINIESTROS: SiniestroResumen[] = [
  {
    id: '11111111-1111-4111-8111-111111111111',
    siniestroId: 'SIN-2041',
    tipo: 'asistido',
    ramo: 'vida-crediticia',
    poliza: 'POL-88421',
    resumen: 'Fallecimiento del asegurado',
    fecha: '2026-09-02',
    estado: 'en_evaluacion',
    resultado: null,
    reserva: 3200000,
    moneda: 'COP',
  },
  {
    id: '22222222-2222-4222-8222-222222222222',
    siniestroId: 'SIN-1988',
    tipo: 'asistido',
    ramo: 'proteccion-dispositivo',
    poliza: 'POL-90102',
    resumen: 'Pantalla rota',
    fecha: '2026-07-11',
    estado: 'pagado',
    resultado: 'aprobado',
    reserva: 420000,
    moneda: 'COP',
  },
];

export const RECHAZADO: SiniestroDetalle = {
  ...SINIESTROS[0],
  estado: 'decidido',
  resultado: 'rechazado',
  descripcion: 'Fallecimiento del asegurado',
  geo: null,
  motivo: 'Documentación incompleta: falta soporte de la factura.',
  historial: [
    { estado: 'recibido', fecha: '2026-09-02T10:00:00Z' },
    { estado: 'en_evaluacion', fecha: '2026-09-02T10:00:02Z' },
    { estado: 'decidido', fecha: '2026-09-03T15:00:00Z' },
  ],
  evidencia: [
    {
      nombre: 'certificado.pdf',
      tipo: 'documento',
      contentType: 'application/pdf',
      url: 'https://s3/firmada',
    },
  ],
  pago: null,
};
