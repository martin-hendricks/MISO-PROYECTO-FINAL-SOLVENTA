import { inject, Pipe, PipeTransform } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { defaultLocale } from './provide-i18n';

/** Decimals each channel currency is shown with. Pinned here instead of
 * trusting each browser's ICU data, which disagrees (Chrome shows COP with 0,
 * Node with 2), so the same premium reads the same everywhere. COP and CLP
 * are quoted without cents locally; others default to 2. */
const DISPLAY_DECIMALS: Record<string, number> = { COP: 0, CLP: 0, MXN: 2, PEN: 2 };

/** Amount with its ISO 4217 code, e.g. `$ 42.300 COP` in es-CO or
 * `$1,234.56 MXN` in es-MX (HU-108). Cents show only when the amount has
 * them; COP/CLP always round to whole units. */
export function formatMoney(amount: number, currency: string, locale: string): string {
  const decimals = DISPLAY_DECIMALS[currency] ?? 2;
  // `trailingZeroDisplay` is ES2023 Intl; the project compiles against ES2022 typings.
  const options: Intl.NumberFormatOptions & { trailingZeroDisplay: 'stripIfInteger' } = {
    style: 'currency',
    currency,
    currencyDisplay: 'narrowSymbol',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
    trailingZeroDisplay: 'stripIfInteger',
  };
  const value = new Intl.NumberFormat(locale, options).format(amount);
  return `${value} ${currency}`;
}

/** ISO date (`YYYY-MM-DD`) or timestamp, read in UTC so the calendar day never shifts. */
export function formatDate(iso: string, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(iso));
}

/** Timestamp in the viewer's time zone, e.g. `16/09/2026, 10:24` in es-CO. */
export function formatDateTime(iso: string, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso));
}

function activeLocale(translate: TranslateService): string {
  return translate.getCurrentLang() ?? defaultLocale;
}

@Pipe({ name: 'svMoney', pure: false })
export class MoneyPipe implements PipeTransform {
  private readonly translate = inject(TranslateService);

  transform(amount: number, currency: string): string {
    return formatMoney(amount, currency, activeLocale(this.translate));
  }
}

@Pipe({ name: 'svDate', pure: false })
export class DatePipe implements PipeTransform {
  private readonly translate = inject(TranslateService);

  transform(iso: string): string {
    return formatDate(iso, activeLocale(this.translate));
  }
}

@Pipe({ name: 'svDateTime', pure: false })
export class DateTimePipe implements PipeTransform {
  private readonly translate = inject(TranslateService);

  transform(iso: string): string {
    return formatDateTime(iso, activeLocale(this.translate));
  }
}
