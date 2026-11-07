import { homeSection, requiredRole, SECTIONS } from './sections';

describe('back-office sections', () => {
  it('exposes exactly six destinations in order', () => {
    expect(SECTIONS).toEqual([
      'clientes',
      'cotizaciones',
      'polizas',
      'avisos',
      'reportes',
      'metricas',
    ]);
  });

  it('keeps Avisos, Polizas, Reportes and Metricas for the operator and the rest for the advisor', () => {
    expect(requiredRole('avisos')).toBe('operador');
    expect(requiredRole('polizas')).toBe('operador');
    expect(requiredRole('reportes')).toBe('operador');
    expect(requiredRole('metricas')).toBe('operador');
    expect(requiredRole('clientes')).toBe('asesor');
    expect(requiredRole('cotizaciones')).toBe('asesor');
  });

  it('lands each role on a section it can open', () => {
    expect(homeSection('asesor')).toBe('clientes');
    expect(homeSection('operador')).toBe('avisos');
    expect(homeSection(null)).toBe('clientes');
  });
});
