import { Role } from '../../core/session/session.service';

export type Section =
  | 'clientes'
  | 'cotizaciones'
  | 'polizas'
  | 'avisos'
  | 'reportes'
  | 'metricas'
  | 'notificaciones';

export const SECTIONS: readonly Section[] = [
  'clientes',
  'cotizaciones',
  'polizas',
  'avisos',
  'reportes',
  'metricas',
  'notificaciones',
];

const ALLOWED_ROLES: Record<Section, readonly Role[]> = {
  clientes: ['asesor', 'operador'],
  cotizaciones: ['asesor'],
  // HU-59/61: renovar y cancelar son exclusivas del operador.
  polizas: ['operador'],
  avisos: ['operador'],
  // HU-62/63: el Gherkin habla de roles "compliance"/"operations", pero
  // este sistema solo tiene cliente/asesor/operador (ver dependencies.py
  // de bff-web) -- ambos reportes se autorizan contra "operador", misma
  // decisión que ya tomó el backend.
  reportes: ['operador'],
  // HU-68/69: dashboard de métricas agregadas, de operación interna --
  // mismo único rol de back-office real que reportes.
  metricas: ['operador'],
  notificaciones: ['operador'],
};

export function allowedRoles(section: Section): readonly Role[] {
  return ALLOWED_ROLES[section];
}

export function admite(section: Section, role: Role | null): boolean {
  return role !== null && allowedRoles(section).includes(role);
}

export function homeSection(role: Role | null): Section {
  return role === 'operador' ? 'avisos' : 'clientes';
}
