# Postman — Solventa

Colección manual para probar de punta a punta los servicios del backend, agrupada por servicio (`api-socios`, `ms-cotizacion`, `bff-web`, `bff-movil`). Cada request trae sus pruebas y encadena las variables que necesita la siguiente (tokens, `cotizacionId`, `Idempotency-Key`). También se puede importar en Bruno o Insomnia.

## Archivos

- `Solventa.postman_collection.json` — requests y pruebas.
- `Solventa - local.postman_environment.json` — servicios con `uvicorn` en tu máquina.
- `Solventa - cluster interno.postman_environment.json` — servicios en EKS vía `kubectl port-forward`.
- `Solventa - AWS.postman_environment.json` — detrás del ALB del Ingress; reemplaza `URL_AWS_ALB` por la URL del ALB.

## Uso

En Postman: **Import** la colección y los environments, selecciona uno y corre la colección (Runner, o request por request).

### Local

| Servicio | Puerto | Arranque |
| --- | --- | --- |
| ms-cotizacion | `8001` | `uvicorn app.main:app --port 8001` (necesita PostgreSQL con las migraciones de `ms-cotizacion/db`) |
| api-socios | `8080` | `MS_COTIZACION_URL=http://localhost:8001 uvicorn app.main:app --port 8080` |
| bff-web | `8000` | `SOLVENTA_TOKEN_SECRET=dev-local-secret uvicorn app.main:app --port 8000` |
| bff-movil | `8002` | `SOLVENTA_TOKEN_SECRET=dev-local-secret uvicorn app.main:app --port 8002` |

### Cluster interno

Los Services son `ClusterIP`, así que hace falta reenviar el puerto antes de correr la colección:

```bash
kubectl port-forward -n solventa svc/api-socios 18080:8080 &
kubectl port-forward -n solventa svc/ms-cotizacion 18000:8000 &
kubectl port-forward -n solventa svc/bff-web 18081:8080 &
kubectl port-forward -n solventa svc/bff-movil 18082:8080 &
```

## Orden recomendado

1. `ms-cotizacion / Health` y `api-socios / Health` — confirma que ambos pods responden.
2. `ms-cotizacion / Listar productos` — trae los códigos de producto reales (semillas cargadas por la migración `apps/backend/ms-cotizacion/db/05_ms_cotizacion_catalogo.sql`) y guarda `productoCodigo` para las siguientes requests.
3. `api-socios / Catálogo` — valida la cadena completa `api-socios → ms-cotizacion`. Si da `503`, revisa que `MS_COTIZACION_URL` en `infra/k8s/values/api-socios.yaml` tenga el puerto `:8000`.
4. `ms-cotizacion / Solicitar cotización` — crea una cotización real contra la BD; genera una `Idempotency-Key` nueva y guarda `cotizacionId`.
5. `ms-cotizacion / Repetir la misma solicitud` — misma `Idempotency-Key`: responde `200` con la misma cotización, sin crear otra.
6. `ms-cotizacion / Reconsultar oferta` — usa el `cotizacionId` de la request anterior.
7. `bff-web` — corre primero los `Ingreso`; dejan `tokenCliente`, `tokenAsesor` y `tokenOperador` para las requests protegidas.
8. `bff-movil` — `Registro` → `Ingreso` (deja `tokenMovil`) → `Inicio del cliente`.

Las credenciales de los BFF son de demo: cualquier correo y contraseña entran, salvo la contraseña `incorrecta`, que devuelve `401`. En bff-web, sin `rol`, un correo que empiece por `operador` entra como operador y cualquier otro como asesor.

## Por línea de comandos

```bash
npx -p newman newman run Solventa.postman_collection.json -e "Solventa - local.postman_environment.json"
npx -p newman newman run Solventa.postman_collection.json -e "Solventa - local.postman_environment.json" --folder bff-web
```

## Agregar un endpoint nuevo

Cada vez que se agregue una ruta a un servicio (o un microservicio nuevo entre a la matrix de `deploy.yml`), agregar aquí la request correspondiente, validada contra el servicio real antes de commitear — no documentar una ruta que no se probó.
