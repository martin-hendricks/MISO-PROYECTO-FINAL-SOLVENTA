# Postman — Solventa

Colección manual contra los microservicios desplegados en EKS, para probar de punta a punta sin depender de `kubectl exec`/pods temporales.

## Archivos

- `Solventa.postman_collection.json` — requests, agrupadas por servicio (`api-socios`, `ms-cotizacion`).
- `Solventa - cluster interno.postman_environment.json` — URLs base vía `kubectl port-forward`.

## Uso

Los Services son `ClusterIP` (sin exposición externa todavía — no hay dominio/ALB público configurado), así que hace falta reenviar el puerto antes de correr la colección:

```bash
kubectl port-forward -n solventa svc/api-socios 18080:8080 &
kubectl port-forward -n solventa svc/ms-cotizacion 18000:8000 &
```

Luego, en Postman: **Import** los dos `.json`, selecciona el environment **Solventa - cluster interno**, y corre la colección (Runner, o request por request).

## Orden recomendado

1. `ms-cotizacion / Health` y `api-socios / Health` — confirma que ambos pods responden.
2. `ms-cotizacion / Listar productos` — trae los códigos de producto reales (semillas cargadas por la migración `apps/backend/ms-cotizacion/db/05_ms_cotizacion_catalogo.sql`) y guarda `productoCodigo` para las siguientes requests.
3. `api-socios / Catálogo` — valida la cadena completa `api-socios → ms-cotizacion`. Si da `503`, revisa que `MS_COTIZACION_URL` en `infra/k8s/values/api-socios.yaml` tenga el puerto `:8000`.
4. `ms-cotizacion / Solicitar cotización` — crea una cotización real contra la BD; guarda `cotizacionId`.
5. `ms-cotizacion / Reconsultar oferta` — usa el `cotizacionId` de la request anterior.

## Agregar un endpoint nuevo

Cada vez que se agregue una ruta a `api-socios` o `ms-cotizacion` (o un microservicio nuevo entre a la matrix de `deploy.yml`), agregar aquí la request correspondiente, validada contra el cluster real antes de commitear — no documentar una ruta que no se probó.
