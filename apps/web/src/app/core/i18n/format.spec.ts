import { formatDate, formatMoney } from './format';

/** Intl may emit NBSP / narrow NBSP between symbol and digits. */
const plain = (s: string) => s.replace(/[  ]/g, ' ');

describe('formatMoney (HU-108, PL-01: formatted on the channel)', () => {
  it('shows the es-MX acceptance example with cents', () => {
    expect(plain(formatMoney(1234.56, 'MXN', 'es-MX'))).toBe('$1,234.56 MXN');
  });

  it('keeps whole amounts without decimals', () => {
    expect(plain(formatMoney(42300, 'COP', 'es-CO'))).toBe('$ 42.300 COP');
    expect(plain(formatMoney(1200, 'MXN', 'es-MX'))).toBe('$1,200 MXN');
  });

  it('pads cents to two digits when the amount has them', () => {
    expect(plain(formatMoney(1234.5, 'PEN', 'es-PE'))).toBe('S/ 1,234.50 PEN');
  });

  it('rounds COP and CLP, quoted without cents locally', () => {
    expect(plain(formatMoney(1234.56, 'CLP', 'es-CL'))).toBe('$1.235 CLP');
    expect(plain(formatMoney(42300.5, 'COP', 'es-CO'))).toBe('$ 42.301 COP');
  });

  it('defaults other currencies to two decimals', () => {
    expect(plain(formatMoney(10.5, 'USD', 'es-CO'))).toBe('$ 10,50 USD');
  });

  it('changes how the premium looks, never its value', () => {
    const co = plain(formatMoney(1234.56, 'MXN', 'es-CO'));
    const mx = plain(formatMoney(1234.56, 'MXN', 'es-MX'));

    expect(co).not.toBe(mx);
    expect(co.replace(/\D/g, '')).toBe(mx.replace(/\D/g, ''));
  });
});

describe('formatDate', () => {
  it('shows the acceptance example date in es-MX', () => {
    expect(formatDate('2026-07-09', 'es-MX')).toBe('09/07/2026');
  });

  it('never shifts the calendar day', () => {
    expect(formatDate('2026-01-01', 'es-CO')).toBe('01/01/2026');
  });
});
