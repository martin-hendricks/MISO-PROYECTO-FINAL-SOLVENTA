/** The single line of business the portal quotes (HU-1): SOAT motocicleta. */
export const RAMO = 'SOAT motocicleta';

/** Risk data the form captures; their valid ranges come from the catalog (HU-2). */
export type CampoRango = 'cilindraje_cc' | 'modelo_anio';

export const CAMPOS_RANGO: readonly CampoRango[] = ['cilindraje_cc', 'modelo_anio'];

export const CAMPO_CIUDAD = 'ciudad_circulacion';

export interface Rango {
  minimo: number;
  maximo: number;
}

export type DatosRiesgo = Record<string, string | number>;

export interface Riesgo {
  cilindraje: string;
  modelo: string;
  ciudad: string;
}

export type ProblemaCampo = 'required' | 'range';

/**
 * `null` when the value is valid. Without a catalog range the core's typed
 * rejection (HU-3) stays the only check.
 */
export function validarRango(rango: Rango | undefined, valor: string): ProblemaCampo | null {
  if (valor.trim() === '') {
    return 'required';
  }
  if (!rango) {
    return null;
  }
  const numero = Number(valor);
  return Number.isInteger(numero) && numero >= rango.minimo && numero <= rango.maximo
    ? null
    : 'range';
}

/** Risk data with the names the core catalog expects. */
export function datosRiesgo(riesgo: Riesgo): DatosRiesgo {
  return {
    cilindraje_cc: Number(riesgo.cilindraje),
    modelo_anio: Number(riesgo.modelo),
    [CAMPO_CIUDAD]: riesgo.ciudad,
  };
}
