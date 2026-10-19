import { InjectionToken } from '@angular/core';

/** Prefix the edge routes to `bff-web` (see `infra/k8s/platform/ingress.yaml`). */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  factory: () => '/web',
});
