import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { LocaleService } from './core/i18n/locale.service';
import { provideSolventaI18n } from './core/i18n/provide-i18n';
import { authInterceptor } from './core/session/auth.interceptor';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    ...provideSolventaI18n(),
    // Instantiate eagerly so <html lang> matches the stored locale on boot,
    // not only after a view that injects LocaleService renders.
    provideAppInitializer(() => {
      inject(LocaleService);
    }),
  ],
};
