import { inject, Pipe, PipeTransform } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { defaultLocale } from './provide-i18n';

/** Amount with its ISO 4217 code, e.g. `$ 42.300 COP` in es-CO. */
export function formatMoney(amount: number, currency: string, locale: string): string {
  const value = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    currencyDisplay: 'narrowSymbol',
    maximumFractionDigits: 0,
  }).format(amount);
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
