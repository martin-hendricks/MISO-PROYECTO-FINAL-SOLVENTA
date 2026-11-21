# Socios caído: reglas del ALB para la API de socios y el back-office de socios

## Objetivo

Que la API de socios externos y la pantalla de socios del back-office sean alcanzables por el ALB y, por el
mapeo de `apigw-mapeo-rutas`, por el API Gateway.

## Problema (comprobado el 2026-11-21 en AWS y en el clúster)

Los servicios están sanos: `api-socios`, `ms-identidad` y `bff-web` corren sin reinicios y sin errores en los
logs. Lo que falla es el camino. Prueba real a través del API Gateway, sin credenciales:

| Petición | Respuesta | Quién responde |
| --- | --- | --- |
| `GET /v1/catalogo` | 401 "API key de socio requerida" | `api-socios` (llega) |
| `GET /v1/cotizaciones` | **503** | ALB, sin regla |
| `GET /v1/originaciones-hipotecarias` | **503** | ALB, sin regla |
| `GET /v1/backoffice/socios` | **503** | ALB, sin regla |

El 503 es la página HTML del ALB: la petición cae al target group por defecto, que está vacío, y no llega a
ningún servicio. En `alb_routes` solo estaba `/v1/catalogo` para `api-socios` y ningún path `/v1/backoffice`
para `bff-web`.

Comparando las OpenAPI de los pods con las reglas vivas: `api-socios` expone 5 rutas y solo 2 tenían regla;
`bff-web` tiene 5 rutas bajo `/v1/backoffice` (socios, credenciales, revocación y perfil del back-office) y
ninguna tenía regla.

## Autenticación de lo que se expone

- `api-socios`: API key de socio y un alcance por ruta (`catalogo:leer`, `cotizaciones:escribir`,
  `originaciones:escribir`), en `app/seguridad.py`. Es la API de socios externos; `/v1/catalogo` ya estaba
  expuesta igual.
- `/v1/backoffice/*` de `bff-web`: JWT con rol `operador` o `asesor` en las cinco rutas.

## Alcance

Dentro: `alb_routes` en `infra/terraform/environments/minimo/variables.tf`.
Fuera: el código de los servicios. Por el diseño de `apigw-mapeo-rutas` el API Gateway toma los paths de la
misma variable, así que no se toca el módulo `edge`.

## Cambios

| Servicio | Path nuevo | Prioridad |
| --- | --- | --- |
| api-socios | `/v1/cotizaciones` | 11 |
| api-socios | `/v1/originaciones-hipotecarias` | 12 |
| bff-web | `/v1/backoffice` | 35 |

Se agregan **después** de los paths existentes de cada servicio: la prioridad de cada regla es
`route.priority + posición` (`modules/alb/main.tf`), así que las reglas que ya existen (10, y 30 a 34) no
cambian de prioridad. Se comprobó que ninguna ruta real de otro servicio empieza por los patrones nuevos, de
modo que no se le quita tráfico a nadie.

Efecto: **tres reglas nuevas en el ALB**, ninguna existente modificada, y seis rutas nuevas en el API Gateway
(32 en total).

## Criterios de aceptación

- [x] `terraform validate` y `terraform fmt` en `environments/minimo`.
- [x] Evaluado con la variable real: prioridades únicas, sin cambio en las reglas existentes (10; 30 a 34 de
      `bff-web`; 40 a 45 de `bff-movil`; 50 de grafana) y 32 rutas en el API Gateway.
- [ ] `terraform plan` y `apply` contra el entorno real.
- [ ] Tras el `apply`, sin credenciales: `GET /v1/cotizaciones`, `GET /v1/originaciones-hipotecarias` y
      `GET /v1/backoffice/socios` pasan de 503 a 401 (llegan al servicio).

## Limitaciones

- **El `plan` real no se pudo hacer desde este checkout**: su `terraform.tfstate` está vacío y propone crear
  todo. Debe correrse donde esté el state vigente y decir `3 to add` en el ALB y `6 to add` en el API Gateway,
  sin destruir ni cambiar nada existente. Si propone mover prioridades de reglas existentes, no se aplica.
- No se probó con credenciales: solo se comprueba que la petición llega al servicio y este la rechaza con 401.
  Que un socio con API key válida cotice, o que un operador abra la pantalla de socios, no se ejercitó.
- Mergear no aplica nada: ningún workflow ejecuta Terraform.
