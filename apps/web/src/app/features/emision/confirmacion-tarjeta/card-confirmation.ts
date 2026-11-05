export type CardFranchise = 'visa' | 'mastercard' | 'amex' | 'diners' | 'unknown';

export function cardFranchise(digits: string): CardFranchise {
  if (digits.startsWith('34') || digits.startsWith('37')) {
    return 'amex';
  }
  if (digits.startsWith('36') || digits.startsWith('38')) {
    return 'diners';
  }
  const three = Number(digits.slice(0, 3));
  if (digits.length >= 3 && three >= 300 && three <= 305) {
    return 'diners';
  }
  if (digits.startsWith('4')) {
    return 'visa';
  }
  const two = Number(digits.slice(0, 2));
  if (digits.length >= 2 && two >= 51 && two <= 55) {
    return 'mastercard';
  }
  const four = Number(digits.slice(0, 4));
  if (digits.length >= 4 && four >= 2221 && four <= 2720) {
    return 'mastercard';
  }
  return 'unknown';
}

export function cardLimit(digits: string): number {
  const franchise = cardFranchise(digits);
  if (franchise === 'amex') {
    return 15;
  }
  if (franchise === 'diners') {
    return 14;
  }
  return 16;
}

/** Digits only, cut at the franchise length. Spaces and extra paste characters do not count. */
export function cardDigits(raw: string): string {
  const digits = raw.replace(/\D/g, '');
  return digits.slice(0, cardLimit(digits));
}

export function groupCard(digits: string): string {
  const only = cardDigits(digits);
  const sizes =
    cardFranchise(only) === 'amex'
      ? [4, 6, 5]
      : cardFranchise(only) === 'diners'
        ? [4, 6, 4]
        : [4, 4, 4, 4];
  const parts: string[] = [];
  let index = 0;
  for (const size of sizes) {
    if (index >= only.length) {
      break;
    }
    parts.push(only.slice(index, index + size));
    index += size;
  }
  return parts.join(' ');
}

/** Two digits. A single month from 2 through 9 gains a leading zero; 0 and 1 wait. */
export function expiryMonth(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 2);
  if (digits.length <= 1) {
    return digits && digits >= '2' ? `0${digits}` : digits;
  }
  const value = Number(digits);
  return value >= 1 && value <= 12 ? digits : expiryMonth(digits.slice(0, -1));
}

export function expiryYear(raw: string): string {
  return raw.replace(/\D/g, '').slice(0, 2);
}

export function cardReady(input: {
  holder: string;
  digits: string;
  month: string;
  year: string;
  code: string;
}): boolean {
  const digits = cardDigits(input.digits);
  const code = input.code.replace(/\D/g, '');
  return (
    input.holder.trim().length > 0 &&
    digits.length === cardLimit(digits) &&
    /^(0[1-9]|1[0-2])$/.test(input.month) &&
    /^\d{2}$/.test(input.year) &&
    /^\d{3,4}$/.test(code)
  );
}
