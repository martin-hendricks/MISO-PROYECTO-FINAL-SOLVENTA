import { Role } from '../../core/session/session.service';

export type Section = 'clientes' | 'cotizaciones' | 'polizas' | 'avisos';

export const SECTIONS: readonly Section[] = ['clientes', 'cotizaciones', 'polizas', 'avisos'];

const REQUIRED_ROLE: Record<Section, Role> = {
  clientes: 'asesor',
  cotizaciones: 'asesor',
  polizas: 'asesor',
  avisos: 'operador',
};

export function requiredRole(section: Section): Role {
  return REQUIRED_ROLE[section];
}

export function homeSection(role: Role | null): Section {
  return role === 'operador' ? 'avisos' : 'clientes';
}
