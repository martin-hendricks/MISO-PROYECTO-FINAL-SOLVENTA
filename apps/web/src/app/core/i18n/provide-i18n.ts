import { Provider } from '@angular/core';
import { provideTranslateLoader, provideTranslateService } from '@ngx-translate/core';
import { CatalogTranslateLoader } from './catalog-translate.loader';

export const defaultLocale = 'es-CO';

export function provideSolventaI18n(): Provider[] {
  return provideTranslateService({
    loader: provideTranslateLoader(CatalogTranslateLoader),
    fallbackLang: defaultLocale,
    lang: defaultLocale,
  });
}
