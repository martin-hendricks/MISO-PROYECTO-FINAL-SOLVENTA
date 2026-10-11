# Solventa — Cliente Web

Portal de escritorio con dos variantes en la misma aplicación: cliente (`/user`) y CMS (`/cms`). Ambas piden sesión; sin ella el portal abre `/login` (HU-103). nginx entrega los archivos estáticos. La autorización por rol queda en `bff-web` (HU-74/75), no en el contenedor.

**Stack:** Angular + TypeScript, `ngx-translate` (`es-CO`, `es-MX`, `es-CL`, `es-PE`)
**Pruebas:** Karma (unitarias), Cucumber/Gherkin + Playwright (E2E)

## Local

```bash
cd apps/web
pnpm install --frozen-lockfile
pnpm test
pnpm start
```

`pnpm start` reenvía `/web/*` a `bff-web` en `http://localhost:8000` (`proxy.conf.json`). Para ingresar en local, levanta el BFF en otra terminal:

```bash
cd apps/backend/bff-web
SOLVENTA_TOKEN_SECRET=<secreto-local> uvicorn app.main:app --port 8000
```

El stub acepta cualquier correo y contraseña, salvo la contraseña `incorrecta`, que responde 401.

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

Los escenarios simulan la respuesta de `/web/sesion/ingreso` en el navegador; no necesitan el BFF.
