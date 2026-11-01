import { fakerES as faker } from '@faker-js/faker';

export const SEED = Number(process.env['E2E_SEED'] ?? 4103);

export interface Credentials {
  email: string;
  password: string;
}

export interface Client {
  clienteId: string;
  nombre: string;
  documento: string;
  canal: 'web' | 'android';
  estado: 'activo' | 'inactivo';
  consentimiento: 'habeas_data' | 'hipotecario_pendiente' | 'revocado';
}

export interface Home {
  ofertaVigente: { cotizacionId: string; ramo: string; estado: string } | null;
  poliza: { numero: string; ramo: string; estado: string } | null;
  siniestroEnCurso: { siniestroId: string; estado: string } | null;
  hipotecario: { estado: string } | null;
}

export interface SignUp {
  nombre: string;
  apellidos: string;
  documento: string;
  correo: string;
  contrasena: string;
}

export function reseed(): void {
  faker.seed(SEED);
}

export function credentials(): Credentials {
  return {
    email: faker.internet.email().toLowerCase(),
    password: faker.internet.password({ length: 12 }),
  };
}

export function signUp(): SignUp {
  return {
    nombre: faker.person.firstName(),
    apellidos: faker.person.lastName(),
    documento: faker.string.numeric(10),
    correo: faker.internet.email().toLowerCase(),
    contrasena: faker.internet.password({ length: 12 }),
  };
}

export function clients(count: number): Client[] {
  return Array.from({ length: count }, (_, index) => ({
    clienteId: `CLI-${index + 1}${faker.string.numeric(3)}`,
    nombre: faker.person.fullName(),
    documento: faker.string.numeric(10),
    canal: faker.helpers.arrayElement(['web', 'android'] as const),
    estado: faker.helpers.arrayElement(['activo', 'inactivo'] as const),
    consentimiento: faker.helpers.arrayElement([
      'habeas_data',
      'hipotecario_pendiente',
      'revocado',
    ] as const),
  }));
}

/** An Inicio with every card: offer, policy in force, open claim and origination. */
export function fullHome(): Home {
  const ramo = faker.helpers.arrayElement([
    'Protección de dispositivo',
    'SOAT motocicleta',
    'Hogar',
  ]);
  return {
    ofertaVigente: {
      cotizacionId: `COT-${faker.string.numeric(4)}`,
      ramo,
      estado: 'oferta_vigente',
    },
    poliza: { numero: `POL-${faker.string.numeric(5)}-CO`, ramo, estado: 'vigente' },
    siniestroEnCurso: { siniestroId: `SIN-${faker.string.numeric(3)}`, estado: 'en_evaluacion' },
    hipotecario: { estado: 'disponible' },
  };
}

export function emptyHome(): Home {
  return { ofertaVigente: null, poliza: null, siniestroEnCurso: null, hipotecario: null };
}

export interface PolicyDetail {
  numero: string;
  ramo: string;
  producto: string;
  resumen: string;
  estado: string;
  venceEn: string;
  inicioVigencia: string;
  finVigencia: string;
  moneda: string;
  primaTotal: number;
  coberturas: { nombre: string; sumaAsegurada: number; deducible: number }[];
  queHacer: string;
}

/** Shape of GET /cliente/polizas/{numero} (bff-web routers/cliente.py, _poliza_billetera + coberturas). */
export function policyDetail(numero: string): PolicyDetail {
  return {
    numero,
    ramo: 'SOAT motocicleta',
    producto: 'SOAT motocicleta',
    resumen: 'Gastos médicos',
    estado: 'VIGENTE',
    venceEn: '2027-10-01T00:00:00Z',
    inicioVigencia: '2026-10-01T00:00:00Z',
    finVigencia: '2027-10-01T00:00:00Z',
    moneda: 'COP',
    primaTotal: 140500,
    coberturas: [{ nombre: 'Gastos médicos', sumaAsegurada: 800, deducible: 0 }],
    queHacer: 'Comunícate con soporte para iniciar el proceso de reclamación.',
  };
}

export interface OperatorPolicy {
  numero: string;
  ramo: string;
  estado: 'vigente' | 'cancelada';
  venceEn: string;
  prima: { valor: number; periodicidad: string };
  renovable: boolean;
  devolucionEstimada: number | null;
  canceladaEn: string | null;
  canceladaPor: string | null;
  motivoCancelacion: string | null;
  siniestrosAbiertos: number | null;
}

/** Shape of GET/POST /operador/polizas/* (bff-web routers/operador.py, _poliza_salida). */
export function operatorPolicy(numero: string): OperatorPolicy {
  return {
    numero,
    ramo: 'Protección de dispositivo',
    estado: 'vigente',
    venceEn: '2027-10-01',
    prima: { valor: 1000, periodicidad: 'ANUAL' },
    renovable: true,
    devolucionEstimada: null,
    canceladaEn: null,
    canceladaPor: null,
    motivoCancelacion: null,
    siniestrosAbiertos: null,
  };
}

export interface Catalog {
  ramo: string;
  nombre: string;
  moneda: string;
  coberturas: { codigo: string; nombre: string; limite: string; unidadLimite: string }[];
  datosRiesgo: (
    | { nombre: string; tipo: 'rango'; minimo: string; maximo: string }
    | { nombre: string; tipo: 'valores'; valores: string[] }
  )[];
}

/** Catalogs as bff-web serves the ms-cotizacion seeds, keyed by the `ramo` the portal sends. */
export const CATALOGS: Record<string, Catalog> = {
  'Protección de dispositivo': {
    ramo: 'Protección de dispositivo',
    nombre: 'Protección de dispositivo',
    moneda: 'COP',
    coberturas: [
      { codigo: 'robo', nombre: 'Robo', limite: '5000000', unidadLimite: 'MONEDA' },
      { codigo: 'dano', nombre: 'Daño accidental', limite: '5000000', unidadLimite: 'MONEDA' },
    ],
    datosRiesgo: [
      { nombre: 'valorDispositivo', tipo: 'rango', minimo: '500000', maximo: '10000000' },
      { nombre: 'marca', tipo: 'valores', valores: ['samsung', 'apple', 'xiaomi', 'motorola'] },
    ],
  },
  'SOAT motocicleta': {
    ramo: 'SOAT motocicleta',
    nombre: 'SOAT motocicleta',
    moneda: 'COP',
    coberturas: [
      {
        codigo: 'muerte',
        nombre: 'Muerte y gastos funerarios',
        limite: '750',
        unidadLimite: 'SMLDV',
      },
    ],
    datosRiesgo: [
      { nombre: 'cilindraje_cc', tipo: 'rango', minimo: '50', maximo: '1800' },
      { nombre: 'modelo_anio', tipo: 'rango', minimo: '2000', maximo: '2026' },
      { nombre: 'ciudad_circulacion', tipo: 'valores', valores: ['bogota', 'medellin', 'cali'] },
    ],
  },
};

export interface Offer {
  cotizacionId: string;
  ramo: string;
  estado: string;
  prima: string;
  primaNeta: string;
  expedicion: string;
  moneda: string;
  venceEn: string;
}

/** A firm offer still valid for a month, as bff-web returns it. */
export function offer(ramo = 'Protección de dispositivo'): Offer {
  const neta = faker.number.int({ min: 60, max: 200 }) * 1000;
  return {
    cotizacionId: faker.string.uuid(),
    ramo,
    estado: 'cotizada',
    prima: `${neta + 9000}.00`,
    primaNeta: `${neta}.00`,
    expedicion: '9000.00',
    moneda: 'COP',
    venceEn: new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString(),
  };
}
