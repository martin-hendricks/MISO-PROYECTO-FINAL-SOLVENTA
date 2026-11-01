/**
 * Lines of business the portal quotes, hard-coded like the Android app
 * (`domain/bff/offer/QuoteLine.kt`): each line has its own form, so the list
 * lives in the channel, not in bff-web. `ramo` and the field keys are the ones
 * mobile sends, so both channels speak the same contract.
 *
 * Only lines with a product in ms-cotizacion are `disponible`; the rest are
 * shown disabled until the core seeds them.
 */
export type TipoCampo = 'moneda' | 'numero' | 'texto' | 'siNo' | 'opciones';

export interface Campo {
  /** Key in `datosRiesgo`. */
  clave: string;
  tipo: TipoCampo;
}

export type RamoId = 'dispositivo' | 'soat' | 'vida' | 'clima' | 'hipotecario' | 'pagos' | 'viaje';

export interface Ramo {
  id: RamoId;
  /** Value sent as `ramo` to bff-web. */
  ramo: string;
  disponible: boolean;
  campos: readonly Campo[];
}

const moneda = (clave: string): Campo => ({ clave, tipo: 'moneda' });
const numero = (clave: string): Campo => ({ clave, tipo: 'numero' });
const texto = (clave: string): Campo => ({ clave, tipo: 'texto' });

export const RAMOS: readonly Ramo[] = [
  {
    id: 'dispositivo',
    ramo: 'Protección de dispositivo',
    disponible: true,
    campos: [
      moneda('valorDispositivo'),
      { clave: 'marca', tipo: 'opciones' },
      texto('modelo'),
      { clave: 'masDe12Meses', tipo: 'siNo' },
    ],
  },
  {
    id: 'soat',
    ramo: 'SOAT motocicleta',
    disponible: true,
    campos: [
      numero('cilindraje_cc'),
      numero('modelo_anio'),
      { clave: 'ciudad_circulacion', tipo: 'opciones' },
    ],
  },
  {
    id: 'vida',
    ramo: 'Microseguro de vida',
    disponible: false,
    campos: [moneda('sumaAsegurada'), numero('edad')],
  },
  {
    id: 'clima',
    ramo: 'Clima y vuelos',
    disponible: false,
    campos: [texto('evento'), texto('referencia'), numero('umbral')],
  },
  {
    id: 'hipotecario',
    ramo: 'Vida hipotecario',
    disponible: false,
    campos: [moneda('valor'), numero('plazoMeses')],
  },
  {
    id: 'pagos',
    ramo: 'Pagos',
    disponible: false,
    campos: [moneda('cuota'), numero('plazoMeses')],
  },
  { id: 'viaje', ramo: 'Viaje', disponible: false, campos: [texto('destino'), numero('duracion')] },
];

export const RAMO_INICIAL: Ramo = RAMOS[0];

export function ramoPorId(id: string): Ramo | undefined {
  return RAMOS.find((ramo) => ramo.id === id);
}

export interface Rango {
  minimo: number;
  maximo: number;
}

export type DatosRiesgo = Record<string, string | number | boolean>;

export type ProblemaCampo = 'required' | 'range' | 'positive' | 'option';

/**
 * `null` when the value is valid. Numbers must be positive integers (as in
 * mobile) and inside the catalog range when the catalog has one; options must
 * be one of the catalog values, which the core checks by membership.
 */
export function validarCampo(
  campo: Campo,
  valor: string,
  rango: Rango | undefined,
  opciones: readonly string[],
): ProblemaCampo | null {
  if (valor.trim() === '') {
    return 'required';
  }
  if (campo.tipo === 'moneda' || campo.tipo === 'numero') {
    const n = Number(valor);
    if (!Number.isInteger(n) || n <= 0) {
      return 'positive';
    }
    return rango && (n < rango.minimo || n > rango.maximo) ? 'range' : null;
  }
  if (campo.tipo === 'opciones') {
    return opciones.includes(valor) ? null : 'option';
  }
  return null;
}

/** `datosRiesgo` with the types the core and mobile use. */
export function datosRiesgo(ramo: Ramo, valores: Readonly<Record<string, string>>): DatosRiesgo {
  const datos: DatosRiesgo = {};
  for (const campo of ramo.campos) {
    const valor = valores[campo.clave] ?? '';
    if (campo.tipo === 'moneda' || campo.tipo === 'numero') {
      datos[campo.clave] = Number(valor);
    } else if (campo.tipo === 'siNo') {
      datos[campo.clave] = valor === 'si';
    } else {
      datos[campo.clave] = valor.trim();
    }
  }
  return datos;
}
