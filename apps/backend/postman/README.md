# Postman — Solventa

Colecciones manuales para probar de punta a punta los servicios del backend (`api-socios`, `ms-cotizacion`, `bff-web`, `bff-movil`). Cada request trae sus pruebas y encadena las variables que necesita la siguiente (tokens, `cotizacionId`, `Idempotency-Key`). También se pueden importar en Bruno o Insomnia.

## Archivos

| Archivo | Para qué |
| --- | --- |
| `local/Solventa local - <servicio>.postman_collection.json` | Una colección por servicio para probar en tu máquina. Traen la URL local en la variable `baseUrl`, no necesitan environment. |
| `Solventa - todos los servicios.postman_collection.json` | Los cuatro servicios en una sola colección. Necesita uno de los environments de abajo. |
| `Solventa - local.postman_environment.json` | URLs de los servicios corriendo con `uvicorn` en tu máquina. |
| `Solventa - EKS por port-forward.postman_environment.json` | Servicios desplegados en EKS, entrando directo a cada Service (`ClusterIP`) con `kubectl port-forward`. |
| `Solventa - EKS por ALB.postman_environment.json` | Servicios desplegados en EKS, entrando por el ALB del Ingress; reemplaza `URL_AWS_ALB` por la URL del ALB. |

## Local

Levanta los servicios desde la carpeta de cada uno (`apps/backend/<servicio>`):

| Servicio | Puerto | Arranque |
| --- | --- | --- |
| ms-cotizacion | `8001` | `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/solventa uvicorn app.main:app --port 8001` (necesita PostgreSQL con las migraciones de `ms-cotizacion/db`) |
| api-socios | `8090` | `MS_COTIZACION_URL=http://localhost:8001 uvicorn app.main:app --port 8090` |
| bff-web | `8000` | `SOLVENTA_TOKEN_SECRET=dev-local-secret uvicorn app.main:app --port 8000` |
| bff-movil | `8002` | `SOLVENTA_TOKEN_SECRET=dev-local-secret uvicorn app.main:app --port 8002` |

api-socios usa `8090` y no `8080` porque ese puerto suele estar ocupado por otros contenedores.

En Postman: **Import** la colección de `local/` del servicio que vas a probar y córrela (Runner, o request por request). Si tu servicio corre en otro puerto, cambia `baseUrl` en las variables de la colección.

## EKS

Importa `Solventa - todos los servicios` y el environment que corresponda, y selecciónalo antes de correr.

Por port-forward, los Services son `ClusterIP`, así que hace falta reenviar el puerto antes de correr la colección:

```bash
kubectl port-forward -n solventa svc/api-socios 18080:8080 &
kubectl port-forward -n solventa svc/ms-cotizacion 18000:8000 &
kubectl port-forward -n solventa svc/bff-web 18081:8080 &
kubectl port-forward -n solventa svc/bff-movil 18082:8080 &
```

## Orden recomendado

1. `ms-cotizacion / Health` y `api-socios / Health` — confirma que ambos servicios responden.
2. `ms-cotizacion / Listar productos` — trae los códigos de producto reales (semillas cargadas por la migración `apps/backend/ms-cotizacion/db/05_ms_cotizacion_catalogo.sql`) y guarda `productoCodigo` para las siguientes requests.
3. `api-socios / Catálogo` — valida la cadena completa `api-socios → ms-cotizacion`. Si da `503`, revisa que ms-cotizacion esté arriba y que `MS_COTIZACION_URL` apunte a él (en EKS, `infra/k8s/values/api-socios.yaml` con el puerto `:8000`).
4. `ms-cotizacion / Solicitar cotización` — crea una cotización real contra la BD; genera una `Idempotency-Key` nueva y guarda `cotizacionId`.
5. `ms-cotizacion / Repetir la misma solicitud` — misma `Idempotency-Key`: responde `200` con la misma cotización, sin crear otra.
6. `ms-cotizacion / Reconsultar oferta` — usa el `cotizacionId` de la request anterior.
7. `bff-web` — corre primero los `Ingreso`; dejan `tokenCliente`, `tokenAsesor` y `tokenOperador` para las requests protegidas.
8. `bff-movil` — `Registro` → `Ingreso` (deja `tokenMovil`) → `Inicio del cliente`.

Las credenciales de los BFF son de demo: cualquier correo y contraseña entran, salvo la contraseña `incorrecta`, que devuelve `401`. En bff-web, sin `rol`, un correo que empiece por `operador` entra como operador y cualquier otro como asesor.

## Por línea de comandos

```bash
npx -p newman newman run "local/Solventa local - bff-web.postman_collection.json"
npx -p newman newman run "Solventa - todos los servicios.postman_collection.json" -e "Solventa - local.postman_environment.json" --folder bff-movil
```

## Agregar un endpoint nuevo

Cada vez que se agregue una ruta a un servicio (o un microservicio nuevo entre a la matrix de `deploy.yml`), agregar la request en `Solventa - todos los servicios` y regenerar o copiar la misma request en la colección de `local/` del servicio, validada contra el servicio real antes de commitear — no documentar una ruta que no se probó.
