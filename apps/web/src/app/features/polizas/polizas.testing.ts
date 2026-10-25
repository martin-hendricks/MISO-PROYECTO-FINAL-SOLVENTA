import { PolizaResumen } from './polizas.gateway';

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
