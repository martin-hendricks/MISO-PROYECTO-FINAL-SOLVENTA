import { PolizaDetalle, PolizaResumen } from './polizas.gateway';

/** Wallet shaped as the proposed `bff-web` contract (HU-149). For specs only. */
export const POLIZAS: PolizaResumen[] = [
  {
    numero: 'POL-2026-00088421',
    producto: 'Hogar',
    estado: 'VIGENTE',
    inicioVigencia: '2026-03-12',
    finVigencia: '2027-03-12',
    moneda: 'COP',
    primaTotal: 42300,
  },
  {
    numero: 'POL-2025-00090102',
    producto: 'SOAT moto',
    estado: 'CANCELADA',
    inicioVigencia: '2025-06-01',
    finVigencia: '2026-06-01',
    moneda: 'COP',
    primaTotal: 148900,
  },
];

export const DETALLE: PolizaDetalle = {
  ...POLIZAS[0],
  coberturas: [
    { nombre: 'Incendio y terremoto', sumaAsegurada: 400000000, deducible: 500000 },
    { nombre: 'Hurto calificado', sumaAsegurada: 40000000, deducible: 200000 },
    { nombre: 'RC familiar', sumaAsegurada: 80000000, deducible: 0 },
  ],
};
