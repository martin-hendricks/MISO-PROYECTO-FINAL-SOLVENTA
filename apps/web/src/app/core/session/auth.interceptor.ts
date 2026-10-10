import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { API_BASE_URL } from '../api/api-base-url';
import { SessionService } from './session.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(SessionService).accessToken();
  const baseUrl = inject(API_BASE_URL);
  if (!token || !req.url.startsWith(`${baseUrl}/`)) {
    return next(req);
  }
  return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};
