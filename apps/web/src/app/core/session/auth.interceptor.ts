import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { API_BASE_URL } from '../api/api-base-url';
import { SessionService } from './session.service';

const RETRY = 'X-Auth-Retry';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const session = inject(SessionService);
  const baseUrl = inject(API_BASE_URL);
  const router = inject(Router);
  const token = session.accessToken();
  const authed =
    token && req.url.startsWith(`${baseUrl}/`)
      ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : req;

  return next(authed).pipe(
    catchError((error) => {
      if (!(error instanceof HttpErrorResponse) || error.status !== 401) {
        return throwError(() => error);
      }
      if (!req.url.startsWith(`${baseUrl}/`) || isOpenSession(req.url) || req.headers.has(RETRY)) {
        return throwError(() => error);
      }
      return session.refresh().pipe(
        catchError(() => {
          const login = router.url.startsWith('/cms') ? '/cms/login' : '/login';
          void router.navigateByUrl(login);
          return throwError(() => error);
        }),
        switchMap(() => {
          const renewed = session.accessToken();
          return next(
            req.clone({
              setHeaders: {
                ...(renewed ? { Authorization: `Bearer ${renewed}` } : {}),
                [RETRY]: '1',
              },
            }),
          );
        }),
      );
    }),
  );
};

function isOpenSession(url: string): boolean {
  return (
    url.includes('/sesion/ingreso') ||
    url.includes('/sesion/refresh') ||
    url.includes('/sesion/salida')
  );
}
