# SOLVENTA_TOKEN_SECRET faltante en ms-pagos y ms-consentimiento

## Objetivo

Que emitir póliza funcione en el clúster y que ningún servicio que valida o firma JWT arranque sin
el secreto del token.

## Problema (observado el 2026-11-21 en el clúster)

`POST /v1/cliente/polizas` falla con 503 en `bff-web`. La cadena:

| Servicio | Síntoma |
| --- | --- |
| `bff-web` | 24 respuestas 503 en 30 min en `POST /v1/cliente/polizas` (traduce el 5xx de abajo) |
| `ms-pagos` | 24 respuestas 500 en `POST /v1/pagos/primas`, sin traceback en el log |

Causa: `ms-pagos/app/seguridad.py` lanza `HTTPException(500, "SOLVENTA_TOKEN_SECRET no configurado")`
cuando la variable está vacía, y el pod de `ms-pagos` no la tiene. Es un 500 deliberado, por eso no
hay traceback. El `values/ms-pagos.yaml` no proyectaba el secreto, a diferencia de `ms-polizas`,
`ms-suscripcion` y el resto. Es el pendiente que `pago-poliza-jwt-servicio` dejó fuera de alcance
(`variablesEntornoSecreto` en los values de `ms-pagos` y `ms-polizas`); `ms-polizas` y
`ms-suscripcion` ya se corrigieron, `ms-pagos` no.

Aseguramiento: de los 13 servicios que usan `SOLVENTA_TOKEN_SECRET` en el código, comprobado dentro
de cada pod, solo faltaba en `ms-pagos` y `ms-consentimiento`. `ms-consentimiento` todavía no había
fallado porque nadie lo había llamado con un token, pero falla igual.

## Alcance

Dentro: `infra/k8s/values/ms-pagos.yaml` y `infra/k8s/values/ms-consentimiento.yaml`.
Fuera: el secreto en sí (ya existe en Secrets Manager como `solventa-minimo-bff-web-token`, con la
clave `SOLVENTA_TOKEN_SECRET`) y el código de los servicios.

## Tareas

| ID | Tarea |
| --- | --- |
| T1 | `ms-pagos`: proyectar `solventa-minimo-bff-web-token` como `ms-pagos-token`. |
| T2 | `ms-consentimiento`: proyectar el mismo secreto como `ms-consentimiento-token`. |

## Criterios de aceptación

- [x] `helm template` de ambos values genera el ExternalSecret `<servicio>-token` y lo inyecta por `envFrom`.
- [ ] Tras el despliegue: `SOLVENTA_TOKEN_SECRET` presente en los 13 pods que lo usan.
- [ ] Tras el despliegue: `POST /v1/pagos/primas` sin 500 y emitir póliza de punta a punta.

## Limitaciones

- El despliegue es automático al mergear a `develop`; hasta entonces el clúster sigue igual.
- Todos los servicios comparten el mismo secreto de token (el de `bff-web`), igual que hoy.
