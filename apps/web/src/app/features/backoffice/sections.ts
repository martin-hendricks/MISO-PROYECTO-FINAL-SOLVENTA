import { Role } from '../../core/session/session.service';

export type Section = 'clientes' | 'cotizaciones' | 'polizas' | 'avisos' | 'reportes';

export const SECTIONS: readonly Section[] = [
  'clientes',
  'cotizaciones',
  'polizas',
  'avisos',
  'reportes',
];

const REQUIRED_ROLE: Record<Section, Role> = {
  clientes: 'asesor',
  cotizaciones: 'asesor',
  // HU-59/61: renovar y cancelar son exclusivas del operador.
  polizas: 'operador',
  avisos: 'operador',
  // HU-62/63: el Gherkin habla de roles "compliance"/"operations", pero
  // este sistema solo tiene cliente/asesor/operador (ver dependencies.py
  // de bff-web) -- ambos reportes se autorizan contra "operador", misma
  // decisión que ya tomó el backend.
  reportes: 'operador',
};

export function requiredRole(section: Section): Role {
  return REQUIRED_ROLE[section];
}

export function homeSection(role: Role | null): Section {
  return role === 'operador' ? 'avisos' : 'clientes';
}
