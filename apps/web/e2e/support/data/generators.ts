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
