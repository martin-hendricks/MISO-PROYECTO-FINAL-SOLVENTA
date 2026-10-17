# Postman — Solventa

Colección manual contra los microservicios desplegados en EKS, para probar de punta a punta sin depender de `kubectl exec`/pods temporales.

## Archivos

- `Solventa.postman_collection.json` — requests, agrupadas por servicio (`api-socios`, `ms-cotizacion`). Cada carpeta usa su propia variable de base URL (`baseUrlApiSocios`, `baseUrlMsCotizacion`), resuelta distinto según el environment.
- `Solventa - API Gateway.postman_environment.json` — **recomendado**: ambas variables apuntan al endpoint público del API Gateway. Prueba la cadena real (API Gateway → VPC Link → ALB → `TargetGroupBinding` → pods, ver `infra/terraform/modules/alb` e `infra/k8s/platform/target-group-bindings.yaml`). No requiere `kubectl` ni estar en la VPC.
- `Solventa - cluster interno.postman_environment.json` — cada variable apunta a un puerto local distinto vía `kubectl port-forward`, para depurar un servicio directo sin pasar por el API Gateway/ALB. No sirve para los dos `Health` (ver más abajo).

## Uso — vía API Gateway (recomendado)

1. Obtén el endpoint actual (cambia en cada `terraform apply`/`destroy`, el ID del API Gateway es aleatorio):
   ```bash
   terraform -chdir=infra/terraform/environments/minimo output -raw api_gateway_endpoint
   ```
2. Actualiza `baseUrlApiSocios` y `baseUrlMsCotizacion` en el environment **Solventa - API Gateway** con ese valor (sin el `/` final).
3. En Postman: **Import** la colección y los dos environments, selecciona **Solventa - API Gateway**, y corre la colección (Runner, o request por request).

Los endpoints `Health` (`/health` de cada servicio) no tienen Listener Rule en el ALB — solo `/v1/catalogo`, `/v1/productos`, `/v1/cotizaciones` — así que vía este environment caen en la regla `default` del ALB y dan `503`. Úsalos con el environment de cluster interno.

## Uso — vía cluster interno (depuración directa)

Los Services son `ClusterIP` (sin exposición externa por sí solos), así que hace falta reenviar el puerto:

```bash
kubectl port-forward -n solventa svc/api-socios 18080:8080 &
kubectl port-forward -n solventa svc/ms-cotizacion 18000:8000 &
```

Luego, en Postman: selecciona el environment **Solventa - cluster interno**, y corre la colección.

## Orden recomendado

1. `ms-cotizacion / Health` y `api-socios / Health` — confirma que ambos pods responden.
2. `ms-cotizacion / Listar productos` — trae los códigos de producto reales (semillas cargadas por la migración `apps/backend/ms-cotizacion/db/05_ms_cotizacion_catalogo.sql`) y guarda `productoCodigo` para las siguientes requests.
3. `api-socios / Catálogo` — valida la cadena completa `api-socios → ms-cotizacion`. Si da `503`, revisa que `MS_COTIZACION_URL` en `infra/k8s/values/api-socios.yaml` tenga el puerto `:8000`.
4. `ms-cotizacion / Solicitar cotización` — crea una cotización real contra la BD; guarda `cotizacionId`.
5. `ms-cotizacion / Reconsultar oferta` — usa el `cotizacionId` de la request anterior.

## Agregar un endpoint nuevo

Cada vez que se agregue una ruta a `api-socios` o `ms-cotizacion` (o un microservicio nuevo entre a la matrix de `deploy.yml`), agregar aquí la request correspondiente, validada contra el cluster real antes de commitear — no documentar una ruta que no se probó.
