import { DOCUMENT } from '@angular/common';
import { inject, Injectable, signal } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { defaultLocale } from './provide-i18n';

export const LOCALES = ['es-CO', 'es-MX', 'es-CL', 'es-PE'] as const;
export type Locale = (typeof LOCALES)[number];

const STORAGE_KEY = 'solventa.locale';

function read(): Locale | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw && (LOCALES as readonly string[]).includes(raw) ? (raw as Locale) : null;
  } catch {
    return null;
  }
}

function write(locale: Locale): void {
  try {
    localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // Storage can be blocked; the choice then only lives for this tab (the
    // TranslateService default still applies via provideSolventaI18n).
  }
}

/** HU-108: idioma/región persists across sessions (unlike SessionService's
 * sessionStorage) because a visitor without an account yet still needs to
 * see login/registro in their chosen locale. */
@Injectable({ providedIn: 'root' })
export class LocaleService {
  private readonly translate = inject(TranslateService);
  private readonly document = inject(DOCUMENT);
  private readonly current = signal<Locale>(read() ?? defaultLocale);

  readonly locale = this.current.asReadonly();

  constructor() {
    this.syncDocumentLang();
  }

  /** Whether the visitor already chose a locale (first-launch gate). */
  hasChosen(): boolean {
    return read() !== null;
  }

  use(locale: Locale): void {
    this.current.set(locale);
    write(locale);
    this.syncDocumentLang();
    void this.translate.use(locale);
  }

  /** Screen readers pick pronunciation from `<html lang>`; index.html only
   * ships the es-CO default, so keep it in step with the active locale. */
  private syncDocumentLang(): void {
    this.document.documentElement.lang = this.current();
  }
}
