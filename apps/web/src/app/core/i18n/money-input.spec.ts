import {
  formatGroupedCop,
  incomeWire,
  moneyDigits,
  spendingWire,
  wireAmount,
} from './money-input';

describe('money input', () => {
  it('groups Colombia digits without changing the numeric value', () => {
    expect(moneyDigits('$4.500.000')).toBe('4500000');
    expect(formatGroupedCop('4500000')).toBe('$4.500.000');
    expect(formatGroupedCop('')).toBe('');
  });

  it('submits two decimal digits without a symbol or grouping', () => {
    expect(wireAmount('4500000')).toBe('4500000.00');
    expect(wireAmount('1200000')).toBe('1200000.00');
    expect(incomeWire('4500000')).toBe('4500000.00');
    expect(spendingWire('0')).toBe('0.00');
  });

  it('rejects zero or negative income and malformed spending', () => {
    expect(incomeWire('0')).toBeNull();
    expect(incomeWire('')).toBeNull();
    expect(spendingWire('')).toBeNull();
    expect(wireAmount('12a')).toBeNull();
  });

  it('rejects an amount too large to represent instead of changing it', () => {
    expect(moneyDigits('1'.repeat(13))).toBe('1'.repeat(12));
    expect(wireAmount('1'.repeat(13))).toBeNull();
  });
});
