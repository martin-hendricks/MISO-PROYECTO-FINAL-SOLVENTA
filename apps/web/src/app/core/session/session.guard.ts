import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { SessionService } from './session.service';

export const requireSession: CanActivateFn = () =>
  inject(SessionService).isActive() ? true : inject(Router).createUrlTree(['/login']);

export const redirectSignedIn: CanActivateFn = () =>
  inject(SessionService).isActive() ? inject(Router).createUrlTree(['/user']) : true;
