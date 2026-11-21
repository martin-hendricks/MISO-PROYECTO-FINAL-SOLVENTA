# API Gateway: mapeo explícito de URLs (sin tocar el ALB)

## Objetivo

Que el API Gateway también tenga el mapeo de URLs por servicio, hoy definido solo en las reglas del ALB,
sin modificar el ALB.

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

## Mapeo (24 rutas = 12 paths × 2)

| Path | Servicio | Prioridad en el ALB |
| --- | --- | --- |
| `/v1/catalogo` | api-socios | 10 |
| `/v1/sesion`, `/v1/registro`, `/v1/cliente`, `/v1/asesor`, `/v1/operador` | bff-web | 30 |
| `/bff-movil/v1/sesion`, `/registro`, `/cliente`, `/docs`, `/openapi.json` | bff-movil | 40 |
| `/observabilidad/grafana` | grafana | 50 |

Cada fila genera `ANY <path>` y `ANY <path>/{proxy+}` en el API Gateway.

## Rutas reales que no tienen regla (el ALB no se tocó)

Se compararon las OpenAPI de los pods con las reglas vivas del ALB. Lo siguiente existe en el servicio y
caería al target group por defecto:

| Ruta | Servicio | Lo usa |
| --- | --- | --- |
| `/bff-movil/v1/identidad/prueba-de-vida` | bff-movil | **La app Android** (`MobileBffApi.kt`: `POST identidad/prueba-de-vida`). Hoy falla en la nube. |
| `/v1/backoffice/*` (5 rutas) | bff-web | La pantalla de socios del back-office |
| `/v1/cotizaciones` (2) y `/v1/originaciones-hipotecarias` (1) | api-socios | Socios externos |

Para cerrarlas basta agregar el path a `alb_routes`; por el diseño de arriba queda también en el API
Gateway. Se deja como decisión aparte porque implica modificar el ALB.

## Criterios de aceptación

- [x] `terraform validate` en `environments/minimo`.
- [x] La expresión evaluada con la variable real genera las 24 rutas esperadas.
- [ ] `terraform plan` y `apply` contra el entorno real (ver limitaciones).
- [ ] Tras el `apply`: el API Gateway muestra las 24 rutas más la comodín y las peticiones siguen respondiendo igual.

## Limitaciones

- **No se pudo hacer `plan` real.** El `terraform.tfstate` de este checkout está vacío (772 bytes, del 6 de
  noviembre) y el plan propone crear todo. El entorno real no se aplicó desde esta carpeta: hay que correr el
  `plan` y el `apply` desde donde esté el state vigente. No aplicar desde aquí.
- Con `apigw_restringir_a_rutas_mapeadas = true` hay que haber cerrado antes las rutas sin regla, o dejarían
  de ser alcanzables (hoy ya fallan en el ALB, pero ahí devuelven el error del target group vacío).
- Los patrones del ALB terminan en `*` (`/v1/cliente*`) y los del API Gateway no: un path como
  `/v1/clientes-x` entraría por la comodín pero no por una ruta mapeada.
