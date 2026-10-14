import { formatDate, formatMoney } from './cotizacion.format';

describe('cotizacion format', () => {
  it('formats the premium for the locale without decimals', () => {
    expect(formatMoney(148900, 'COP', 'es-CO')).toBe('$148.900');
    expect(formatMoney(8000000, 'COP', 'es-CO')).toBe('$8.000.000');
  });

  it('follows the grouping of each market', () => {
    expect(formatMoney(148900, 'MXN', 'es-MX')).toBe('$148,900');
  });

  it('shows the expiry as the calendar day the core sent', () => {
    expect(formatDate('2026-10-01', 'es-CO')).toBe('01/10/2026');
    expect(formatDate('2026-09-22T23:30:00Z', 'es-CO')).toBe('22/09/2026');
  });
});
