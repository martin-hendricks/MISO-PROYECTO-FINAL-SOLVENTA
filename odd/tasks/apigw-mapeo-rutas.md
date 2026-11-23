# API Gateway: mapeo explícito de URLs, y la regla de `identidad` que faltaba en el ALB

## Objetivo

1. Que el API Gateway también tenga el mapeo de URLs por servicio, hoy definido solo en las reglas del ALB,
   sin modificar las reglas existentes del ALB.
2. Cerrar el hueco que dejaba la prueba de vida de la app Android sin regla en el ALB: una regla nueva,
   `/bff-movil/v1/identidad`.

## Situación (revisada el 2026-11-21 en AWS)

El API Gateway (`solventa-minimo-api`, HTTP API) tiene **una sola ruta comodín** `ANY /{proxy+}`, con
integración `HTTP_PROXY` por VPC Link hacia el listener del ALB. No tiene mapeo propio: cualquier path
llega al ALB y es el ALB quien decide a qué servicio va. Lo que no coincide con ninguna regla cae al
target group por defecto, que está vacío.

## Diseño

El módulo `edge` recibe `var.routes`, la misma variable `alb_routes` que arma las reglas del ALB. Cada
path genera dos rutas hacia la misma integración: `ANY <path>` y `ANY <path>/{proxy+}` (el proxy greedy no
incluye la raíz). Una sola fuente de verdad: agregar un path a `alb_routes` lo deja en los dos.

`apigw_restringir_a_rutas_mapeadas` (por defecto `false`) controla la ruta comodín:

- `false`: las rutas mapeadas existen y la comodín se queda. **El comportamiento no cambia.**
- `true`: se quita la comodín y solo pasan los paths mapeados; el resto responde 404 en el borde y ni
  llega al ALB.

La comodín pasa a tener índice (`proxy[0]`); un bloque `moved` evita que Terraform la destruya y la recree.

## Mapeo (26 rutas = 13 paths × 2)

| Path | Servicio | Prioridad en el ALB |
| --- | --- | --- |
| `/v1/catalogo` | api-socios | 10 |
| `/v1/sesion`, `/v1/registro`, `/v1/cliente`, `/v1/asesor`, `/v1/operador` | bff-web | 30 |
| `/bff-movil/v1/sesion`, `/registro`, `/cliente`, `/docs`, `/openapi.json` | bff-movil | 40 a 44 |
| `/bff-movil/v1/identidad` (nueva) | bff-movil | 45 |
| `/observabilidad/grafana` | grafana | 50 |

Cada fila genera `ANY <path>` y `ANY <path>/{proxy+}` en el API Gateway.

## Regla nueva en el ALB: `/bff-movil/v1/identidad`

La app Android llama `POST identidad/prueba-de-vida` (`MobileBffApi.kt`) y el ALB no tenía regla para esa ruta.
La petición caía al target group por defecto, que está vacío, y el ALB respondía 503. Comprobado el
2026-11-21 contra el API Gateway real:

| Petición | Respuesta antes |
| --- | --- |
| `GET /bff-movil/v1/cliente/polizas` | 401 "Token requerido" (llega a `bff-movil`) |
| `POST /bff-movil/v1/identidad/prueba-de-vida` | **503 del ALB** (no llega) |

La ruta nunca estuvo en `alb_routes`: las reglas de `bff-movil` se añadieron el 2026-11-01 y la prueba de vida
se implementó el 2026-11-11. Se agrega **al final** de la lista de paths de `bff-movil` a propósito: la
prioridad de cada regla es `route.priority + posición` (`modules/alb/main.tf`), así que queda con la 45 y las
cinco reglas que ya existen (40 a 44) no cambian de prioridad. Insertarla en medio las habría corrido.

Efecto en el ALB: **una regla nueva de listener**, ninguna existente modificada.

## Rutas reales que siguen sin regla (no se cambian aquí)

| Ruta | Servicio | Lo usa |
| --- | --- | --- |
| `/v1/backoffice/*` (5 rutas) | bff-web | La pantalla de socios del back-office |
| `/v1/cotizaciones` (2) y `/v1/originaciones-hipotecarias` (1) | api-socios | Socios externos |

Cerrarlas es agregar el path a `alb_routes`; por el diseño de arriba queda también en el API Gateway.

## Criterios de aceptación

- [x] `terraform validate` en `environments/minimo`.
- [x] La expresión evaluada con la variable real genera las 26 rutas esperadas, y las prioridades de `bff-movil` quedan 40, 41, 42, 43, 44 (sin cambio) y 45 (`identidad`).
- [ ] `terraform plan` y `apply` contra el entorno real (ver limitaciones).
- [ ] Tras el `apply`: el API Gateway muestra las 26 rutas más la comodín, las peticiones siguen respondiendo igual y `POST /bff-movil/v1/identidad/prueba-de-vida` da 401 (llega a `bff-movil`) en lugar de 503.

## Limitaciones

- **No se pudo hacer `plan` real.** El `terraform.tfstate` de este checkout está vacío (772 bytes, del 6 de
  noviembre) y el plan propone crear todo. El entorno real no se aplicó desde esta carpeta: hay que correr el
  `plan` y el `apply` desde donde esté el state vigente. No aplicar desde aquí.
- Con `apigw_restringir_a_rutas_mapeadas = true` hay que haber cerrado antes las rutas que siguen sin regla,
  o dejarían de ser alcanzables (hoy ya fallan en el ALB, pero ahí devuelven el error del target group vacío).
- El `plan` del ALB debería mostrar `1 to add` (la regla de `identidad`) y ningún cambio en las reglas existentes. Si
  muestra cambios de prioridad en las de `bff-movil`, algo se movió y no debe aplicarse.
- Los patrones del ALB terminan en `*` (`/v1/cliente*`) y los del API Gateway no: un path como
  `/v1/clientes-x` entraría por la comodín pero no por una ruta mapeada.
