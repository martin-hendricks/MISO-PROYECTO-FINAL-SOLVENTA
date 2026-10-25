/**
 * The single line of business the portal quotes (HU-1): SOAT motocicleta.
 *
 * The valid ranges mirror the catalog ms-cotizacion seeds
 * (`db/05_ms_cotizacion_catalogo.sql`). bff-web does not expose that catalog
 * yet (pending on SOLV-165); until it does, this copy lets the form block the
 * CTA before quoting, and the core's typed rejection (HU-3) stays the source
 * of truth on submit.
 */
export const RAMO = 'SOAT motocicleta';

export const CIUDADES = ['bogota', 'medellin', 'cali', 'barranquilla', 'bucaramanga'] as const;

export interface Rango {
  minimo: number;
  maximo: number;
}

export const RANGOS = {
  cilindraje_cc: { minimo: 50, maximo: 1800 },
  modelo_anio: { minimo: 2000, maximo: 2026 },
} as const satisfies Record<string, Rango>;

export type CampoRango = keyof typeof RANGOS;

export type DatosRiesgo = Record<string, string | number>;

export interface Riesgo {
  cilindraje: string;
  modelo: string;
  ciudad: string;
}

export type ProblemaCampo = 'required' | 'range';

/** `null` when the value is valid for its catalog range. */
export function validarRango(campo: CampoRango, valor: string): ProblemaCampo | null {
  if (valor.trim() === '') {
    return 'required';
  }
  const numero = Number(valor);
  const { minimo, maximo } = RANGOS[campo];
  return Number.isInteger(numero) && numero >= minimo && numero <= maximo ? null : 'range';
}

/** Risk data with the names the core catalog expects. */
export function datosRiesgo(riesgo: Riesgo): DatosRiesgo {
  return {
    cilindraje_cc: Number(riesgo.cilindraje),
    modelo_anio: Number(riesgo.modelo),
    ciudad_circulacion: riesgo.ciudad,
  };
}
