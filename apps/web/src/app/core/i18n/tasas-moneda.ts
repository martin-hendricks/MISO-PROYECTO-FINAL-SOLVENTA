import { Rango } from '../../features/cotizacion/ramos';

/** Pesos colombianos por 1 unidad. La misma tabla que ms-cotizacion (`domain/moneda.py`). */
export const COP_POR_UNIDAD: Record<string, number> = {
  COP: 1,
  MXN: 220,
  CLP: 4.5,
  PEN: 1100,
};

/**
 * Rango de un monto, expresado en la moneda que el visitante tiene seleccionada.
 * El catálogo guarda el rango en la moneda del producto (COP). Se redondea hacia
 * dentro para que un entero aceptado aquí siga dentro del rango del núcleo.
 */
export function rangoEnMoneda(rango: Rango, origen: string, destino: string): Rango {
  const desde = COP_POR_UNIDAD[origen];
  const hacia = COP_POR_UNIDAD[destino];
  if (!desde || !hacia || origen === destino) {
    return rango;
  }
  const factor = desde / hacia;
  return {
    minimo: Math.ceil(rango.minimo * factor),
    maximo: Math.floor(rango.maximo * factor),
  };
}
