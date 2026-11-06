const MAX_DIGITS = 12;

/** Digits kept while editing. Grouping, symbols and a leading zero are display only. */
export function moneyDigits(raw: string): string {
  const digits = raw.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
  return digits.slice(0, MAX_DIGITS);
}

/** Colombia display, for example `$4.500.000`. */
export function formatGroupedCop(digits: string): string {
  if (!digits) {
    return '';
  }
  return `$${digits.replace(/\B(?=(\d{3})+(?!\d))/g, '.')}`;
}

/** Wire value with exactly two fraction digits, or null when the digits are not an amount. */
export function wireAmount(digits: string): string | null {
  if (!/^\d+$/.test(digits) || digits.length > MAX_DIGITS) {
    return null;
  }
  return `${digits}.00`;
}

export function validIncome(digits: string): boolean {
  return wireAmount(digits) !== null && wireAmount(digits) !== '0.00';
}

export function validSpending(digits: string): boolean {
  return wireAmount(digits) !== null;
}

export function incomeWire(digits: string): string | null {
  return validIncome(digits) ? wireAmount(digits) : null;
}

export function spendingWire(digits: string): string | null {
  return validSpending(digits) ? wireAmount(digits) : null;
}
