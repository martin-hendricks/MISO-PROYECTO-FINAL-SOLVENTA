# Postman — Solventa

Colección manual contra los microservicios desplegados en EKS, para probar de punta a punta sin depender de `kubectl exec`/pods temporales.

## Archivos

- `Solventa.postman_collection.json` — requests, agrupadas por servicio: `bff-web`, `bff-movil`, `api-socios`, `ms-cotizacion`, `ms-identidad`, `ms-pagos`, `ms-perfilamiento`, `ms-polizas`, `ms-siniestros`, `ms-suscripcion`. Cada carpeta usa su propia variable de base URL (`baseUrl<Servicio>`), resuelta distinto según el environment. No incluye `ms-consentimiento` ni `ms-parametrico` (solo tienen `README.md`, sin código real todavía), ni `analitica`/`notificaciones` (consumidores async de Kafka/MSK, sin API HTTP).
- `Solventa - API Gateway.postman_environment.json` — **recomendado solo para `api-socios`, `bff-web` y `bff-movil`**: son los únicos tres servicios con Listener Rule propia en el ALB (`infra/terraform/environments/minimo/variables.tf`, `var.alb_routes`). Prueba la cadena real (API Gateway → VPC Link → ALB → `TargetGroupBinding` → pods). No requiere `kubectl` ni estar en la VPC.
- `Solventa - cluster interno.postman_environment.json` — cada variable apunta a un puerto local distinto vía `kubectl port-forward`. **Es el único environment que sirve para los `ms-*` internos** (`ms-cotizacion`, `ms-identidad`, `ms-pagos`, `ms-perfilamiento`, `ms-polizas`, `ms-siniestros`, `ms-suscripcion`): ninguno tiene Listener Rule en el ALB a propósito, para que el canal web/móvil solo entre por los BFF y nunca salte directo al núcleo. Tampoco sirve para los dos `Health` (ver más abajo).

## Particularidad de bff-movil: el prefijo `/bff-movil/v1`

El pod de `bff-movil` registra cada router (sesión, registro, cliente) **tres veces**: sin prefijo, con `/v1`, y con `/bff-movil/v1`. Solo la tercera variante ejecuta la lógica real contra el núcleo -- las otras dos devuelven datos *stub* fijos o 404 según el path. Es además el único prefijo que el ALB real enruta. Por eso **todas las requests de la carpeta `bff-movil` usan el path completo `/bff-movil/v1/...` de forma literal**, lo que funciona igual contra el API Gateway y contra el pod vía port-forward (el mismo registro triple expone también ese prefijo en local) -- no hace falta variar el path según el environment.

## ⚠️ Inconsistencia conocida: `baseUrlMsCotizacion` en el environment "API Gateway"

Ese valor sigue apuntando al mismo endpoint del API Gateway por herencia del archivo original, pero **no funciona**: `ms-cotizacion` no tiene Listener Rule en el ALB (excluido a propósito en `var.alb_routes`, mismo motivo que arriba). Cualquier request de la carpeta `ms-cotizacion` corrida con ese environment cae en la regla `default` del ALB y da `503`. No se corrigió en esta actualización para no tocar algo fuera del alcance pedido -- usar siempre el environment **cluster interno** para `ms-cotizacion`. Al agregar los `ms-*` nuevos no se repitió este mismo valor equivocado: ninguno tiene `baseUrl` en el environment "API Gateway".

## Uso — vía API Gateway (recomendado para api-socios, bff-web, bff-movil)

1. Obtén el endpoint actual (cambia en cada `terraform apply`/`destroy`, el ID del API Gateway es aleatorio):
   ```bash
   terraform -chdir=infra/terraform/environments/minimo output -raw api_gateway_endpoint
   ```
2. Actualiza `baseUrlApiSocios`, `baseUrlBffWeb` y `baseUrlBffMovil` en el environment **Solventa - API Gateway** con ese valor (sin el `/` final).
3. En Postman: **Import** la colección y los dos environments, selecciona **Solventa - API Gateway**, y corre la colección (Runner, o request por request).

Los endpoints `Health` (`/health` de cada servicio) no tienen Listener Rule en el ALB, así que vía este environment caen en la regla `default` del ALB y dan `503`. Úsalos con el environment de cluster interno.

## Uso — vía cluster interno (depuración directa, obligatorio para los ms-* internos)

Los Services son `ClusterIP` (sin exposición externa por sí solos), así que hace falta reenviar el puerto. Solo levanta los port-forwards de los servicios que vayas a probar:

```bash
kubectl port-forward -n solventa svc/api-socios        18080:8080 &
kubectl port-forward -n solventa svc/ms-cotizacion      18000:8000 &
kubectl port-forward -n solventa svc/bff-web            18001:8000 &
kubectl port-forward -n solventa svc/bff-movil          18002:8000 &
kubectl port-forward -n solventa svc/ms-identidad       18003:8080 &
kubectl port-forward -n solventa svc/ms-pagos           18004:8080 &
kubectl port-forward -n solventa svc/ms-perfilamiento   18005:8080 &
kubectl port-forward -n solventa svc/ms-polizas         18006:8080 &
kubectl port-forward -n solventa svc/ms-siniestros      18007:8080 &
kubectl port-forward -n solventa svc/ms-suscripcion     18008:8080 &
```

Luego, en Postman: selecciona el environment **Solventa - cluster interno**, y corre la colección.

## Orden recomendado (flujo representativo, no exhaustivo)

**Canal web (bff-web), de punta a punta:**

1. `bff-web / Sesión y registro / Registro cliente` (o `Ingreso cliente` si el usuario ya existe) — guarda `accessTokenCliente`.
2. `bff-web / Cliente / Solicitar cotización` — guarda `cotizacionIdCliente`.
3. `bff-web / Cliente / Emitir póliza` — orquesta ms-cotizacion → ms-pagos → ms-polizas; guarda `numeroPolizaCliente`.
4. `bff-web / Cliente / Billetera de pólizas` y `Detalle de póliza` — confirma que la póliza emitida aparece.
5. `bff-web / Sesión y registro / Ingreso asesor` e `Ingreso operador` — guarda `accessTokenAsesor`/`accessTokenOperador` para el resto del flujo.
6. `bff-web / Asesor / Solicitar cotización (asesor)` → `Consultar decisión de emisión` → `Firmar y emitir póliza (asesor)` — camino alterno de emisión vía asesor (HU-149: separa evaluar de emitir).
7. `bff-web / Operador / Detalle de póliza (operador)` → `Renovar póliza` / `Cancelar póliza` / `Modificar coberturas` — ciclo de vida de la póliza emitida en el paso 3.

**Canal móvil (bff-movil):** mismo flujo que el canal web, carpeta `bff-movil` (`Ingreso` → `Solicitar cotización` → `Aceptar cotización` → `Emitir póliza` → `Reportar siniestro`), todas con el prefijo `/bff-movil/v1/*`.

**api-socios + ms-cotizacion (cadena directa, sin BFF):**

1. `ms-cotizacion / Health` y `api-socios / Health` — confirma que ambos pods responden (solo con el environment de cluster interno).
2. `ms-cotizacion / Listar productos` — trae los códigos de producto reales (semillas cargadas por la migración `apps/backend/ms-cotizacion/db/05_ms_cotizacion_catalogo.sql`) y guarda `productoCodigo`.
3. `api-socios / Catálogo` — valida la cadena completa `api-socios → ms-cotizacion`. Si da `503`, revisa que `MS_COTIZACION_URL` en `infra/k8s/values/api-socios.yaml` tenga el puerto `:8000`.
4. `ms-cotizacion / Solicitar cotización` → `Aceptar oferta` — crea una cotización real y la acepta; guarda `cotizacionId`/`ofertaId`.

**Microservicios internos aislados (depuración puntual):** `ms-identidad` (alta + autenticación), `ms-pagos` (cobro de prima), `ms-perfilamiento` (consentimiento + oferta hipotecaria), `ms-polizas` (ciclo de vida completo sin pasar por el BFF), `ms-siniestros` (evento paramétrico, reporte de cliente, cambio de estado), `ms-suscripcion` (evaluar decisión aislada) -- cada carpeta es independiente y no requiere correr las demás primero, salvo por los valores que uses en el body (UUIDs de ejemplo via `{{$guid}}` si no tienes uno real a mano).

## Agregar un endpoint nuevo

Cada vez que se agregue una ruta a cualquiera de los servicios de esta colección (o un microservicio nuevo entre a la matrix de `deploy.yml` y tenga API HTTP real), agregar aquí la request correspondiente, validada contra el cluster real antes de commitear — no documentar una ruta que no se probó.
