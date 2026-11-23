# Pago/emisión de póliza: autenticación service-to-service rota

## Objetivo

Que el flujo `POST /v1/cliente/polizas` (aceptar oferta → cobrar prima → emitir póliza)
funcione de punta a punta en local, y que un reintento tras una falla técnica retome el
flujo en vez de quemar la cotización.

## Problema

El commit `fe46f12` ("feat(ms-pagos, ms-suscripcion): exigir JWT valido en los endpoints")
exigió `LlamanteDep` en ms-pagos y ms-suscripcion, pero los llamadores internos siguen
llamando sin `Authorization` y esos dos servicios no aceptan `rol="servicio"`.

Cadena rota:

| Llamador | Llamada | Estado |
|---|---|---|
| ms-cotizacion | `POST ms-suscripcion/v1/suscripciones` | 401 Token requerido |
| ms-pagos | `GET ms-suscripcion/v1/suscripciones/{id}` | 401 Token requerido |
| ms-polizas | `GET ms-suscripcion/v1/suscripciones/{id}` | 401 Token requerido |
| ms-polizas | `GET ms-pagos/v1/pagos/{id}` | 401 Token requerido |
| ms-cotizacion | `GET ms-perfilamiento/v1/ofertas-hipotecario/...` | 401 (degradado, prima con factor de respaldo) |

Con token `rol="servicio"` también da 401 "Token invalido" porque `ROLES` de ms-suscripcion y
ms-pagos no incluye `"servicio"` (ms-perfilamiento y ms-consentimiento sí lo aceptan).

Efecto secundario: `_idempotency_key()` en `bff-web/app/routers/cliente.py` genera un uuid4
por request. Como la aceptación se confirma antes de llamar a ms-suscripcion, el primer
intento deja la cotización `aceptada` y los reintentos chocan con `oferta_ya_usada` (422).

## Alcance autorizado

- `apps/backend/ms-cotizacion/app/infrastructure/{suscripciones,adaptador_perfil_perfilamiento}.py` + `main.py`
- `apps/backend/ms-pagos/app/{infrastructure/externos.py,infrastructure/token_servicio.py*,main.py,seguridad.py}`
- `apps/backend/ms-polizas/app/{infrastructure/precondiciones.py,infrastructure/token_servicio.py*,main.py}`
- `apps/backend/ms-suscripcion/app/seguridad.py`
- `apps/backend/bff-web/app/routers/cliente.py`
- Tests unitarios de esos módulos (`*/tests/*`)

`*` archivo nuevo, copiando el patrón ya existente en `ms-cotizacion/app/infrastructure/token_servicio.py`.

Fuera de alcance (se reporta como pendiente): wiring `SOLVENTA_TOKEN_SECRET` en
`infra/k8s/values/{ms-pagos,ms-polizas}.yaml` (`variablesEntornoSecreto`).

## Criterios de aceptación

- [x] Rama `fix/pago-poliza-jwt-service-to-service` creada desde `origin/develop` (b0046ad).
- [x] Toda llamada interna a ms-suscripcion/ms-pagos/ms-perfilamiento envía Bearer de servicio.
- [x] ms-suscripcion y ms-pagos aceptan `rol="servicio"` en `ROLES` (y `uid=None` para
      tokens de servicio: el token lleva el nombre del emisor, no un UUID).
- [x] `POST /v1/cliente/polizas` con cotización nueva devuelve `EMITIDA` y deja filas en
      `ms_suscripcion.suscripcion`, `ms_pagos.pago` y `ms_polizas.poliza`.
- [x] Reintentar la misma cotización (misma Idempotency-Key derivada) no devuelve
      `oferta_ya_usada`.
- [x] Suites pytest de ms-cotizacion, ms-pagos, ms-polizas, ms-suscripcion y bff-web en verde.
- [x] Tests nuevos que fijen el header `Authorization` saliente y el rol `servicio`.

## Tareas

| ID | Tarea | Ruta | Verificación |
|---|---|---|---|
| T1 | Rama desde develop actualizado | git | `git rev-parse --abbrev-ref HEAD` |
| T2 | ms-suscripcion acepta rol servicio | inline | `pytest` ms-suscripcion |
| T3 | ms-pagos: token saliente + rol servicio | delegada (writer) | `pytest` ms-pagos |
| T4 | ms-polizas: token saliente a suscripcion y pagos | delegada (writer) | `pytest` ms-polizas |
| T5 | ms-cotizacion: token a suscripcion y perfilamiento | delegada (writer) | `pytest` ms-cotizacion |
| T6 | bff-web: Idempotency-Key determinista en `emitir` | delegada (writer) | `pytest` bff-web |
| T7 | E2E contra docker compose | inline (parent) | curl + psql |

Ruta elegida: delegada directa (un solo writer) para T3–T6 por tocar 2+ archivos no triviales
por servicio; T1/T2/T7 inline por ser mecánicas o de verificación.

## Evidencia

- `docker compose logs ms-cotizacion`: `POST http://ms-suscripcion:8080/v1/suscripciones 401`
  seguido de `503` en `/{id}/aceptacion`; `bff-web`: `servicio no disponible: ms-cotizacion`.
- BD antes del fix: `ms_suscripcion.suscripcion = 0`, `ms_pagos.pago = 0`, `ms_polizas.poliza = 0`.
- `22f918a4-04e6-4e47-890d-188068ef69fa` quedó `estado='aceptada'` (cotización quemada).
- curl: sin token 401 "Token requerido"; con rol servicio 401 "Token invalido"; con rol
  cliente 404 "no_encontrado" (auth correcta).

## Progreso

- T1 completada.
- T2–T6 completadas por el writer delegado, un commit por work unit:
  - `3a35be6` ms-suscripcion: rol `servicio` + `uid=None` para tokens de servicio.
  - `4574fb0` ms-pagos: `token_servicio.py`, header en `SuscripcionesHTTP`, `ROLES`.
  - `82cf48a` ms-polizas: token a ms-suscripcion y ms-pagos en `precondiciones.py`.
  - `0ae30f1` ms-cotizacion: token a ms-suscripcion y a perfilamiento.
  - `54e75a4` bff-web: `Idempotency-Key` derivada de la cotización al emitir.
- T7 completada (E2E contra docker compose, imágenes reconstruidas).

### Hallazgo adicional del fix

Agregar `"servicio"` a `ROLES` no bastaba: `exigir_llamante` hacía
`UUID(str(payload["uid"]))` y el token de servicio lleva el nombre del emisor en `uid`
(`"ms-cotizacion"`, `"ms-pagos"`, `"ms-polizas"`), así que la coerción lanzaba `ValueError`
→ 500. Se resolvió con `uid: UUID | None` y `None` cuando el rol es `servicio`.

## Evidencia E2E (2026-11-14)

- Registro + login de cliente nuevo vía bff-web; cotización `39b67eb0` (SOAT moto) →
  `POST /v1/cliente/polizas` → `200 {"resultado":"EMITIDA","numero":"POL-2026-00000001"}`.
- Filas persistidas: `ms_suscripcion.suscripcion` (ACEPTADA), `ms_pagos.pago` (APROBADO,
  140500.00) y `ms_polizas.poliza` (VIGENTE).
- Reintento de la misma cotización: `200` con la MISMA póliza `POL-2026-00000001` (idempotente,
  sin `oferta_ya_usada`).
- Regresión del bug original: con `ms-suscripcion` detenido, la emisión da `503`; al
  levantarlo, el reintento de la misma cotización devuelve `200 EMITIDA`
  (`POL-2026-00000002`) en vez de `422 oferta_ya_usada`.
- `401 Unauthorized` en logs de ms-cotizacion/ms-suscripcion/ms-pagos/ms-polizas/
  ms-perfilamiento desde el reinicio: 0.
- `GET /v1/ofertas-hipotecario/clientes/{id}/ultima` desde ms-cotizacion: `200 OK`; la prima
  de vida-hipotecario usa el factor real (188250.60) en vez del respaldo (192000.00).
- Spot check del padre: `ms-cotizacion` → `186 passed, 1 skipped, 7 deselected`.

## Pendiente fuera de alcance

- Wiring de `SOLVENTA_TOKEN_SECRET` en `infra/k8s/values/ms-pagos.yaml` y
  `infra/k8s/values/ms-polizas.yaml` (`variablesEntornoSecreto`): en el cluster esos
  servicios no reciben el secreto, así que el mismo 500 aparecería en los `GET` internos.
  `ms-polizas.yaml` ya proyecta `solventa-minimo-bff-web-token` como `ms-polizas-token`
  pero no lo monta como variable.

## Próximo paso

Revisión/PR de la rama `fix/pago-poliza-jwt-service-to-service` contra `develop`.
