import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { LocaleService } from '../i18n/locale.service';
import { Role, SessionService } from './session.service';

export function requireRole(roles: readonly Role[], loginUrl: string): CanActivateFn {
  return () => (inject(SessionService).hasRole(roles) ? true : inject(Router).parseUrl(loginUrl));
}

export function redirectSignedIn(roles: readonly Role[], homeUrl: string): CanActivateFn {
  return () => (inject(SessionService).hasRole(roles) ? inject(Router).parseUrl(homeUrl) : true);
}

/** HU-108: a first-time visitor (no locale chosen yet, no session either --
 * a returning signed-in customer keeps whatever locale they last chose and
 * is never sent back here) lands on idioma-region before registro/login. */
export const requireLocaleChosen: CanActivateFn = () => {
  if (inject(LocaleService).hasChosen() || inject(SessionService).isActive()) {
    return true;
  }
  return inject(Router).createUrlTree(['/idioma-region']);
};
