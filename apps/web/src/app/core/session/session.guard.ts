import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Role, SessionService } from './session.service';

export function requireRole(roles: readonly Role[], loginUrl: string): CanActivateFn {
  return () => (inject(SessionService).hasRole(roles) ? true : inject(Router).parseUrl(loginUrl));
}

export function redirectSignedIn(roles: readonly Role[], homeUrl: string): CanActivateFn {
  return () => (inject(SessionService).hasRole(roles) ? inject(Router).parseUrl(homeUrl) : true);
}
