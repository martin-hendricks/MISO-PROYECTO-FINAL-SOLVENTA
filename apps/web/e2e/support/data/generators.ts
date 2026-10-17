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

export function reseed(): void {
  faker.seed(SEED);
}

export function credentials(): Credentials {
  return {
    email: faker.internet.email().toLowerCase(),
    password: faker.internet.password({ length: 12 }),
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
