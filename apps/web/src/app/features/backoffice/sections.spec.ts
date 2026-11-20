import { admite, allowedRoles, homeSection, SECTIONS } from './sections';

describe('back-office sections', () => {
  it('exposes the destinations in order, including notificaciones', () => {
    expect(SECTIONS).toEqual([
      'clientes',
      'socios',
      'cotizaciones',
      'polizas',
      'avisos',
      'reportes',
      'metricas',
      'notificaciones',
    ]);
  });

  it('keeps operator sections for the operator and quotes for the advisor', () => {
    expect(allowedRoles('avisos')).toEqual(['operador']);
    expect(allowedRoles('polizas')).toEqual(['operador']);
    expect(allowedRoles('reportes')).toEqual(['operador']);
    expect(allowedRoles('metricas')).toEqual(['operador']);
    expect(allowedRoles('notificaciones')).toEqual(['operador']);
    expect(allowedRoles('cotizaciones')).toEqual(['asesor']);
    expect(allowedRoles('clientes')).toEqual(['asesor', 'operador']);
  });

  it('opens socios to both the advisor and the operator', () => {
    expect(allowedRoles('socios')).toEqual(['asesor', 'operador']);
    expect(admite('socios', 'asesor')).toBeTrue();
    expect(admite('socios', 'operador')).toBeTrue();
    expect(admite('socios', 'cliente')).toBeFalse();
  });

  it('hides notificaciones from the advisor and keeps clientes for both roles', () => {
    expect(admite('notificaciones', 'asesor')).toBeFalse();
    expect(admite('notificaciones', 'operador')).toBeTrue();
    expect(admite('clientes', 'asesor')).toBeTrue();
    expect(admite('clientes', 'operador')).toBeTrue();
  });

  it('lands each role on a section it can open', () => {
    expect(homeSection('asesor')).toBe('clientes');
    expect(homeSection('operador')).toBe('avisos');
    expect(homeSection(null)).toBe('clientes');
  });
});
