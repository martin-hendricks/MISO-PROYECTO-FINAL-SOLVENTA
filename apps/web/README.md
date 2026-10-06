# Solventa — Cliente Web

Portal de escritorio con dos variantes en la misma aplicación: cliente (`/user`) y CMS (`/cms`). nginx entrega los archivos estáticos. La autorización por rol queda en `bff-web` (HU-74/75), no en el contenedor.

**Stack:** Angular + TypeScript, `ngx-translate` (`es-CO`, `es-MX`, `es-CL`, `es-PE`)
**Pruebas:** Karma (unitarias), Cucumber/Gherkin + Playwright (E2E)

## Local

```bash
cd apps/web
pnpm install --frozen-lockfile
pnpm test
pnpm start
```

## Imagen

```bash
cd apps/web
docker compose up --build
```

El portal queda en `http://localhost:8080`.

## E2E

Con el contenedor en el puerto 8080:

```bash
cd apps/web
pnpm exec playwright install chromium
BASE_URL=http://localhost:8080 pnpm e2e
```
