# Solventa — Cliente Web

Portal de escritorio con dos variantes en la misma aplicación: cliente (`/user`) y back-office de asesor y operador (`/cms`, HU-8). Cada una pide la sesión de su rol: sin ella el cliente llega a `/login` (HU-103) y el back-office a `/cms/login`. nginx entrega los archivos estáticos. La autorización por rol queda en `bff-web` (HU-74/75), no en el contenedor.

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

El stub acepta cualquier correo y contraseña, salvo la contraseña `incorrecta`, que responde 401. En `/cms/login` el rol lo asigna el BFF: un correo que empieza por `operador` entra como operador y cualquier otro como asesor.

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

Los escenarios simulan las respuestas del BFF en el navegador (`e2e/support/doubles`); no necesitan el BFF.

Los `.feature` se organizan por flujo en `e2e/features/<flujo>/` y cada uno lleva el tag del flujo; los escenarios llevan el tag de su HU y su clave SOLV para trazabilidad.

| Flujo | Tag |
| --- | --- |
| Acceso | `@access` |
| Portal cliente | `@customer-portal` |
| Back-office | `@backoffice` |
| Cotización | `@quotation` |
| Suscripción y emisión | `@subscription` |
| Siniestros | `@claims` |
| Ciclo de vida de póliza | `@policy-lifecycle` |

```bash
BASE_URL=http://localhost:8080 pnpm e2e --tags @backoffice
BASE_URL=http://localhost:8080 pnpm e2e --tags @HU-103
pnpm e2e:pending
```

- Los escenarios `@pendiente` mapean el Gherkin de las HU web aún no implementadas; `pnpm e2e` los excluye y `pnpm e2e:pending` los lista sin ejecutarlos. Al implementar la HU se quita el tag y se escriben sus steps.
- Los datos de prueba son pseudoaleatorios con semilla fija (`E2E_SEED`, por defecto `4103`); la semilla queda adjunta en el reporte para reproducir la corrida.
- El reporte queda en `e2e/reports/cucumber-report.html` con un screenshot por paso; en los PR (`Web Unit+E2E`) se publica como artifact `web-e2e-report` solo cuando la corrida falla y se conserva 7 días.

### Evidencia para el cliente

El workflow manual `Web E2E Evidence (manual)` (Actions → Run workflow) corre las unitarias y luego el E2E sobre la rama elegida, y siempre publica:

- `web-e2e-evidence-<rama>-<corrida>`: reporte HTML con un screenshot por paso.
- `web-unit-coverage-<rama>-<corrida>`: reporte de cobertura de las unitarias.

Recibe `tags` opcionales (`@backoffice`, `@HU-103`; vacío corre todos los escenarios activos) y los días de retención (30 por defecto).
