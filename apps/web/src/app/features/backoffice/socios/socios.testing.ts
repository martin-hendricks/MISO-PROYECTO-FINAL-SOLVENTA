import { Socio, SocioCreado } from './socios.gateway';

export const ACTIVO_ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
export const REVOCADO_ID = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
export const VIGENTE_ID = 'c1c1c1c1-c1c1-4c1c-8c1c-c1c1c1c1c1c1';
export const ANTERIOR_ID = 'c2c2c2c2-c2c2-4c2c-8c2c-c2c2c2c2c2c2';

export const SOCIOS: Socio[] = [
  {
    socioId: ACTIVO_ID,
    nombre: 'Aliado local',
    alcances: ['catalogo:leer', 'cotizaciones:escribir'],
    estado: 'activo',
    creadoEn: '2026-11-19T10:00:00Z',
    credenciales: [
      { credencialId: VIGENTE_ID, creadaEn: '2026-11-19T10:00:00Z', revocadaEn: null },
      {
        credencialId: ANTERIOR_ID,
        creadaEn: '2026-11-18T09:00:00Z',
        revocadaEn: '2026-11-19T09:30:00Z',
      },
    ],
  },
  {
    socioId: REVOCADO_ID,
    nombre: 'Banco retirado',
    alcances: ['originaciones:escribir'],
    estado: 'revocado',
    creadoEn: '2026-11-10T08:00:00Z',
    credenciales: [
      {
        credencialId: 'c5c5c5c5-c5c5-4c5c-8c5c-c5c5c5c5c5c5',
        creadaEn: '2026-11-12T08:00:00Z',
        revocadaEn: null,
      },
      {
        credencialId: 'c3c3c3c3-c3c3-4c3c-8c3c-c3c3c3c3c3c3',
        creadaEn: '2026-11-10T08:00:00Z',
        revocadaEn: '2026-11-15T08:00:00Z',
      },
    ],
  },
];

export const CREADO: SocioCreado = {
  socioId: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
  nombre: 'Nuevo aliado',
  alcances: ['catalogo:leer'],
  estado: 'activo',
  creadoEn: '2026-11-20T12:00:00Z',
  credencialId: 'c4c4c4c4-c4c4-4c4c-8c4c-c4c4c4c4c4c4',
  apiKey: 'sk_nueva_clave_123',
};
