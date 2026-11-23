import { EstadoSiniestro, ResultadoSiniestro } from './siniestros.gateway';

/** Una sola clave de texto por caso: el cliente ve "Rechazado" o "Aprobado" en vez del
 * estado técnico `decidido`. El estado nunca se comunica solo por color (Figma HU-27). */
export function claveEstado(estado: EstadoSiniestro, resultado: ResultadoSiniestro): string {
  if (estado === 'decidido' && resultado) {
    return `siniestros.estado.${resultado}`;
  }
  return `siniestros.estado.${estado}`;
}
