import { POLIZAS } from '../polizas/polizas.testing';
import { Motivo, ResultadoEmision } from './emision.gateway';

/** Answers shaped as the proposed `bff-web` contract (HU-149). For specs only. */
export const EMITIDA: ResultadoEmision = { resultado: 'EMITIDA', poliza: POLIZAS[0] };

export const MOTIVO: Motivo = {
  codigo: 'RIESGO_FUERA_DE_APETITO',
  mensaje: 'Riesgo fuera de apetito para este producto en la región seleccionada.',
};

export const RECHAZADA: ResultadoEmision = { resultado: 'RECHAZADA', motivo: MOTIVO };
