import { InjectionToken } from '@angular/core';

/**
 * Base URL for API requests.
 *
 * '/web' is the local-dev/placeholder value, routed by bff-web -- not
 * deployed yet (no Dockerfile; see infra/k8s/values/bff-web.yaml, already
 * prepared). In production this string is replaced in build time by
 * .github/workflows/deploy-web.yml with the real API Gateway endpoint
 * (it changes on every `terraform destroy`/`apply`, so it can never be
 * committed here) -- the SPA then talks directly to the API Gateway
 * (api-socios, ms-cotizacion). Routes bff-web would resolve (/sesion/*,
 * /asesor/*) will keep failing until that service is deployed.
 */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  factory: () => '/web',
});
