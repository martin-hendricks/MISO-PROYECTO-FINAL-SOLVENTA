import { TestBed } from '@angular/core/testing';
import { TranslateService } from '@ngx-translate/core';
import { LocaleService } from './locale.service';
import { defaultLocale, provideSolventaI18n } from './provide-i18n';

const STORAGE_KEY = 'solventa.locale';

describe('LocaleService', () => {
  function setup() {
    TestBed.configureTestingModule({ providers: [...provideSolventaI18n()] });
    return {
      locale: TestBed.inject(LocaleService),
      translate: TestBed.inject(TranslateService),
    };
  }

  beforeEach(() => localStorage.removeItem(STORAGE_KEY));
  afterEach(() => localStorage.removeItem(STORAGE_KEY));

  it('defaults to es-CO and reports no choice made yet', () => {
    const { locale } = setup();

    expect(locale.locale()).toBe(defaultLocale);
    expect(locale.hasChosen()).toBeFalse();
  });

  it('persists the choice and switches the active translation language', () => {
    const { locale, translate } = setup();

    locale.use('es-MX');

    expect(locale.locale()).toBe('es-MX');
    expect(locale.hasChosen()).toBeTrue();
    expect(localStorage.getItem(STORAGE_KEY)).toBe('es-MX');
    expect(translate.getCurrentLang()).toBe('es-MX');
  });

  it('starts from a previously stored choice on a new instance', () => {
    localStorage.setItem(STORAGE_KEY, 'es-PE');
    const { locale } = setup();

    expect(locale.locale()).toBe('es-PE');
    expect(locale.hasChosen()).toBeTrue();
  });

  it('keeps <html lang> in step with the active locale', () => {
    localStorage.setItem(STORAGE_KEY, 'es-CL');
    const { locale } = setup();

    expect(document.documentElement.lang).toBe('es-CL');

    locale.use('es-MX');

    expect(document.documentElement.lang).toBe('es-MX');
  });

  it('ignores a corrupted/unknown stored value and falls back to the default', () => {
    localStorage.setItem(STORAGE_KEY, 'fr-FR');
    const { locale } = setup();

    expect(locale.locale()).toBe(defaultLocale);
    expect(locale.hasChosen()).toBeFalse();
  });
});
