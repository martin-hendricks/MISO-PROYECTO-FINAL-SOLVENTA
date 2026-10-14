/** The core sends amount and currency code; the channel formats them for its locale. */
export function formatMoney(amount: number, currency: string, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    currencyDisplay: 'narrowSymbol',
    maximumFractionDigits: 0,
  })
    .format(amount)
    .replace(/\s/g, '');
}

/** `isoDate` is a calendar date (`2026-10-01`) or an instant; it is shown as the UTC day. */
export function formatDate(isoDate: string, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(isoDate));
}
