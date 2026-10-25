import { EmisionAsesor, Paso, SolicitudEmision } from './asesor-emision.gateway';

/** Answers shaped as the proposed `bff-web` contract (HU-149). For specs only. */
const pasos = (emision: Paso['estado'], poliza: Paso['estado']): Paso[] => [
  { paso: 'COTIZAR', estado: 'COMPLETADO' },
  { paso: 'OFERTA', estado: 'COMPLETADO' },
  { paso: 'EMISION', estado: emision },
  { paso: 'POLIZA', estado: poliza },
];

const solicitud = {
  solicitudId: 'SOL-0091',
  cliente: { clienteId: 'CLI-18', nombre: 'Andrés Gómez Molina' },
  producto: 'SOAT motocicleta',
  referencia: 'ABC12D',
  oferta: {
    moneda: 'COP',
    primaTotal: 148900,
    primaNeta: 132400,
    expedicion: 16500,
    vigenciaMeses: 12,
  },
};

export const APROBADA: SolicitudEmision = {
  ...solicitud,
  pasos: pasos('ACTUAL', 'PENDIENTE'),
  decision: {
    resultado: 'ACEPTADA',
    regla: 'Dentro de apetito de riesgo',
    detalle: 'A · sin siniestralidad previa',
    decididoPor: 'Motor automático',
    decididoEn: '2026-09-16T15:24:00Z',
  },
};

export const RECHAZADA: SolicitudEmision = {
  ...solicitud,
  pasos: pasos('ERROR', 'PENDIENTE'),
  decision: {
    resultado: 'RECHAZADA',
    regla: 'Cilindraje fuera de apetito',
    detalle: '1.400 cc supera el máximo de 1.200 cc',
    decididoPor: 'Motor automático',
    decididoEn: '2026-09-16T15:24:00Z',
  },
};

export const EMITIDA: EmisionAsesor = {
  pasos: pasos('COMPLETADO', 'COMPLETADO'),
  firma: { firmadaEn: '2026-09-16T15:25:00Z', hash: '3f9a0c' },
  poliza: {
    numero: 'POL-2026-00090102',
    expedidaEn: '2026-09-16T15:25:01Z',
    inicioVigencia: '2026-09-16',
    finVigencia: '2027-09-16',
  },
};
