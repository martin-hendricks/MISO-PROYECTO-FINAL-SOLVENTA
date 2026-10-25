import { HttpErrorResponse } from '@angular/common/http';
import { Catalogo, Oferta } from './cotizacion.gateway';

/** Answers shaped as bff-web's `/v1/{cliente,asesor}/cotizaciones`. For specs only. */
export const OFERTA_WIRE = {
  cotizacionId: 'COT-4471',
  ramo: 'Protección de dispositivo',
  estado: 'cotizada',
  prima: '128500.00',
  moneda: 'COP',
  venceEn: '2026-11-24T15:00:00Z',
};

export const OFERTA: Oferta = {
  ...OFERTA_WIRE,
  prima: 128500,
  primaNeta: undefined,
  expedicion: undefined,
};

/** Answer with the premium breakdown (SOLV-103). */
export const OFERTA_DESGLOSE_WIRE = { ...OFERTA_WIRE, primaNeta: '120000', expedicion: '8500' };

/** `/v1/{cliente,asesor}/catalogo/{ramo}` as bff-web serves the ms-cotizacion seeds. */
export const CATALOGO_DISPOSITIVO_WIRE = {
  ramo: 'Protección de dispositivo',
  nombre: 'Protección de dispositivo',
  moneda: 'COP',
  coberturas: [
    { codigo: 'robo', nombre: 'Robo', limite: '5000000', unidadLimite: 'MONEDA' },
    { codigo: 'dano', nombre: 'Daño accidental', limite: '5000000', unidadLimite: 'MONEDA' },
    {
      codigo: 'reposicion',
      nombre: 'Reposición por equipo nuevo',
      limite: '5000000',
      unidadLimite: 'MONEDA',
    },
  ],
  datosRiesgo: [
    { nombre: 'valorDispositivo', tipo: 'rango', minimo: '500000', maximo: '10000000' },
    { nombre: 'marca', tipo: 'valores', valores: ['samsung', 'apple', 'xiaomi', 'motorola'] },
  ],
};

export const CATALOGO_SOAT_WIRE = {
  ramo: 'SOAT motocicleta',
  nombre: 'SOAT motocicleta',
  moneda: 'COP',
  coberturas: [{ codigo: 'muerte', nombre: 'Muerte y gastos funerarios', limite: '750' }],
  datosRiesgo: [
    { nombre: 'cilindraje_cc', tipo: 'rango', minimo: '50', maximo: '1800' },
    { nombre: 'modelo_anio', tipo: 'rango', minimo: '2000', maximo: '2026' },
    { nombre: 'ciudad_circulacion', tipo: 'valores', valores: ['bogota', 'medellin', 'cali'] },
  ],
};

export const CATALOGO_DISPOSITIVO: Catalogo = {
  ramo: 'Protección de dispositivo',
  nombre: 'Protección de dispositivo',
  moneda: 'COP',
  coberturas: [
    { codigo: 'robo', nombre: 'Robo' },
    { codigo: 'dano', nombre: 'Daño accidental' },
    { codigo: 'reposicion', nombre: 'Reposición por equipo nuevo' },
  ],
  datosRiesgo: [
    { nombre: 'valorDispositivo', tipo: 'rango', minimo: 500000, maximo: 10000000 },
    { nombre: 'marca', tipo: 'valores', valores: ['samsung', 'apple', 'xiaomi', 'motorola'] },
  ],
};

export const CATALOGO_SOAT: Catalogo = {
  ramo: 'SOAT motocicleta',
  nombre: 'SOAT motocicleta',
  moneda: 'COP',
  coberturas: [{ codigo: 'muerte', nombre: 'Muerte y gastos funerarios' }],
  datosRiesgo: [
    { nombre: 'cilindraje_cc', tipo: 'rango', minimo: 50, maximo: 1800 },
    { nombre: 'modelo_anio', tipo: 'rango', minimo: 2000, maximo: 2026 },
    { nombre: 'ciudad_circulacion', tipo: 'valores', valores: ['bogota', 'medellin', 'cali'] },
  ],
};

export const FUERA_DE_RANGO = {
  codigo: 'dato_riesgo_fuera_de_rango',
  mensaje: "'valorDispositivo' fuera de rango: 500000 a 10000000",
};

export const fueraDeRango = () => new HttpErrorResponse({ status: 422, error: FUERA_DE_RANGO });
