import { InjectionToken } from '@angular/core';

/**
 * Base URL for API requests.
 *
 * '/web' is the local-dev value: proxy.conf.json rewrites it to bff-web's
 * versioned prefix (/web/sesion/... -> /v1/sesion/...). In production this
 * string is replaced in build time by .github/workflows/deploy-web.yml with
 * the real API Gateway endpoint plus '/v1' (the endpoint changes on every
 * `terraform destroy`/`apply`, so it can never be committed here). Gateways
 * build unversioned paths (`${baseUrl}/cliente/...`); the version lives only
 * in this base URL. Keep the factory line below byte-for-byte: the deploy
 * step matches it literally.
 */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  factory: () => '/web',
});
