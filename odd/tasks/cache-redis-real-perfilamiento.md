# Caché de perfil (CacheOF/CacheOD): que funcione de verdad en local y en la nube

## Objetivo

Que la caché Redis de `ms-perfilamiento` funcione extremo a extremo: en local contra un
Redis del compose y en la nube contra ElastiCache, y que un fallo de conexión no pase
desapercibido. Es el primer paso de la estrategia de caché del servicio; el resto (perfil vencido
como respaldo, presupuesto de respuesta, circuit breaker y coalescencia) va en la tarea
`cache-estrategia-resiliente-perfilamiento`.

## Problema (auditado el 2026-11-21 contra `develop` en `4c832500`)

| Dónde | Hallazgo |
| --- | --- |
| `ms-perfilamiento/app/main.py` | El cliente se crea con `Redis(host, port)`: sin contraseña ni TLS. ElastiCache tiene `transit_encryption_enabled = true` y `auth_token`, así que la conexión no se establecería. |
| `AdaptadorConCache` | Traga cualquier excepción de la caché (`except Exception`). Con la conexión rota el servicio responde igual, sin caché y sin avisar. |
| `infra/k8s/values/ms-perfilamiento.yaml` | `REDIS_CACHE_OD_HOST` es el placeholder `cache-od.solventa.internal` (TODO). Terraform crea un único grupo de replicación, no `cache-od` y `cache-of` por separado. |
| `infra/k8s/values/ms-cotizacion.yaml` | Define `REDIS_CACHE_OF_HOST`/`_TTL`, pero ningún código de `ms-cotizacion` lee Redis. Configuración muerta. |
| Terraform | El token de ElastiCache es un `output` sensible, pero no se guarda en Secrets Manager, así que ningún pod lo puede recibir por External Secrets. |
| `apps/backend/docker-compose.yml` | No tiene Redis: en el stack local la caché queda siempre desactivada. |
| Tests | Todos usan fakes. Ninguno habló nunca con un Redis real. |

## Alcance

Dentro: `apps/backend/ms-perfilamiento/`, `apps/backend/docker-compose.yml`,
`infra/terraform/modules/secrets/`, `infra/terraform/environments/minimo/main.tf` y
`infra/k8s/` (values de `ms-perfilamiento` y `ms-cotizacion`, README).

Fuera (tarea `cache-estrategia-resiliente-perfilamiento`): circuit breaker, coalescencia, perfil
vencido en Redis compartido y métricas. Fuera sin tarea todavía: alarmas de la caché y la decisión
sobre cachear en `ms-cotizacion`.

## Diseño

- **Un solo código, dos entornos, por variables de entorno.**
  - Local: Redis plano del compose, sin token ni TLS.
  - Nube: ElastiCache con `REDIS_CACHE_OD_SSL=true` y `REDIS_CACHE_OD_PASSWORD` desde el secreto.
- **Host y token por External Secrets, no fijos en el values.** Terraform publica
  `solventa-minimo-redis-cache` con `host`, `port` y `auth_token`, y el chart los proyecta como
  variables de entorno. Así desaparecen los placeholders y el host sigue al failover.
- **`PING` al arrancar.** Registra `cache redis conectada` o una advertencia con la causa. Nunca
  tumba el servicio: la caché es opcional.

## Tareas

| ID | Tarea |
| --- | --- |
| T1 | `REDIS_CACHE_OD_PASSWORD`, `REDIS_CACHE_OD_SSL` y `TIMEOUT_CACHE_ARRANQUE_MS` en `config.py`, pasados a `Redis(...)`; `verificar_conexion` (PING) al arrancar. |
| T2 | Servicio `cache` (Redis 7.4) en el compose raíz y variable `REDIS_CACHE_OD_HOST` en `ms-perfilamiento`, también en el compose del servicio, con healthcheck. |
| T3 | Tests unitarios del token, el TLS y el PING, y test de integración contra un Redis real (con y sin `requirepass`). |
| T4 | Terraform: secreto `redis-cache` en `modules/secrets` con el endpoint y el token de ElastiCache, conectado en `environments/minimo`. |
| T5 | k8s: `ms-perfilamiento` proyecta el secreto y activa el TLS; `ms-cotizacion` pierde las variables muertas; README al día. |

## Criterios de aceptación

- [x] Unitarias de `ms-perfilamiento` en verde (120) con los archivos tocados al 100%.
- [x] Integración contra Redis real en verde: ida y vuelta con TTL, la caché evitando la segunda
      llamada al proveedor, PING y rechazo sin token (4 tests; se saltan solos sin Redis).
- [x] Imagen real arrancada en Docker: con Redis sano loguea `cache redis conectada`; con un host
      inexistente arranca igual y loguea la advertencia con la causa.
- [x] `docker compose config` válido en el compose raíz y el del servicio.
- [x] `terraform validate` en `environments/minimo`.
- [x] `helm template` de `ms-perfilamiento` proyecta host y token desde `ms-perfilamiento-redis`.
- [ ] `terraform apply` y despliegue en el clúster, con el PING de arranque en el log del pod.

## Orden de despliegue (importante)

1. `terraform apply` en `environments/minimo`: crea el secreto `solventa-minimo-redis-cache`.
2. Desplegar `ms-perfilamiento` con los values nuevos.

Al revés, el pod referencia un secreto inexistente y no arranca (`CreateContainerConfigError`).
External Secrets refresca cada hora; para forzarlo, reiniciar el ExternalSecret.

## Limitaciones

- El camino TLS más token **no está probado**: ElastiCache vive en subredes privadas y no hay
  forma de ejercerlo desde local. Se valida al desplegar, con el PING de arranque.
- No se corrió `terraform plan` ni `apply`: solo `validate`. El desajuste de formato de `main.tf`
  (`terraform fmt`) ya existía en `develop` y no se tocó.
- El token queda en el state local de Terraform y en el secreto, igual que las credenciales de BD.
