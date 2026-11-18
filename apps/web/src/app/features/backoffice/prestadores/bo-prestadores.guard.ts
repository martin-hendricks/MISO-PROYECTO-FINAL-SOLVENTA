import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { SessionService } from '../../../core/session/session.service';

/** Form routes are operador only. An asesor goes back to the list. */
export const soloOperadorPrestadores: CanActivateFn = () => {
  if (inject(SessionService).role() === 'operador') {
    return true;
  }
  return inject(Router).parseUrl('/cms/prestadores');
};
