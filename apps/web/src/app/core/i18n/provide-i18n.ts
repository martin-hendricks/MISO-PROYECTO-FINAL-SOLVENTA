import { Provider } from '@angular/core';
import { provideTranslateLoader, provideTranslateService } from '@ngx-translate/core';
import { CatalogTranslateLoader } from './catalog-translate.loader';

export const defaultLocale = 'es-CO';

const STORAGE_KEY = 'solventa.locale';
const VALID_LOCALES = ['es-CO', 'es-MX', 'es-CL', 'es-PE'];

/** Reads the HU-108 choice directly from storage (not LocaleService) so the
 * app boots in the right locale on the very first render -- before any
 * component has had a chance to inject LocaleService. */
function storedLocale(): string {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw && VALID_LOCALES.includes(raw) ? raw : defaultLocale;
  } catch {
    return defaultLocale;
  }
}

export function provideSolventaI18n(): Provider[] {
  const lang = storedLocale();
  return provideTranslateService({
    loader: provideTranslateLoader(CatalogTranslateLoader),
    fallbackLang: defaultLocale,
    lang,
  });
}
