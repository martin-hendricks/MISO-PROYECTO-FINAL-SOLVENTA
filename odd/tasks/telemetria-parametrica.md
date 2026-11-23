# Canal de telemetría paramétrica: ApiTelemetria → TopicoTelemetria → MotorParametrico

## Objetivo

Alinear el código con la arquitectura aprobada (semana 8, tácticas de concurrencia +
contrapresión y Fachada/Adaptador; EC-ESC-03/04, HA-11): que un evento externo de
telemetría entre por `:ApiTelemetria`, se traduzca en `:AdaptadorTelemetria`, se persista
en `:TopicoTelemetria` y lo procese `:MotorParametrico`, que evalúa y paga sin
intervención humana.

## Problema

| # | Hallazgo | Dónde |
|---|---|---|
| 1 | La cadena paramétrica confirmaba hasta 7 transacciones por evento. Si el proceso caía a la mitad, el siniestro quedaba en `en_evaluacion` sin evaluación y cada reingesta respondía 500 (`RuntimeError` en `_resultado_existente`): el evento no se completaba nunca. Incumple EC-ESC-04. | `ms-siniestros/app/application/casos_uso.py` |
| 2 | `desembolsar()` se llamaba antes del commit: una transacción que luego fallaba dejaba un desembolso sin pago registrado. | ídem |
| 3 | En PostgreSQL la colisión de `evento_id` salta en el `flush` de `agregar`, no en `confirmar`: la carrera terminaba en `IntegrityError` sin traducir (500). | `ms-siniestros/app/infrastructure/sql.py` |
| 4 | `POST /v1/eventos-parametricos` solo bloqueaba a `cliente`: un `asesor` podía disparar pagos con umbral y monto arbitrarios. | `ms-siniestros/app/api/v1/rutas.py` |
| 5 | `ms-parametrico` vacío, `TopicoTelemetria` sin crear (`auto.create.topics.enable=false`), sin consumidor. | `apps/backend/ms-parametrico`, `infra/` |

## Decisiones

- **D5, opción B.** `ms-parametrico` es solo la ingesta (`:ApiTelemetria` + adaptadores +
  productor, sin BD). El `:MotorParametrico` es un consumidor dentro de `ms-siniestros`, que
  ya es dueño del siniestro, la evaluación, el pago y la billetera. Coincide con el par
  `:MsSiniestros`–`:MotorParametrico` de la semana 8. La opción A (motor en `ms-parametrico`)
  obligaba a mover tablas y la billetera.
- **Dos pasos con el efecto externo en medio.** Una transacción registra, evalúa y deja el
  pago registrado en `enrutado`; después se desembolsa y otra transacción cierra en
  `pagado`. Un pago a medias (`enrutado` con pago) se completa en la reingesta.
- **Idempotencia del desembolso.** La llamada al adaptador es al-menos-una-vez, siempre con
  la misma clave `evento_id`; el contrato del puerto exige idempotencia por clave. Es lo que
  impide el pago doble, también con entregas concurrentes (ver evidencia de integración).
- **Contrapresión explícita.** 202 solo con ack del tópico (`acks=all`, productor
  idempotente). Cupo de publicaciones en vuelo por réplica: lleno → 429 + `Retry-After`;
  broker caído o lento → 503 + `Retry-After`. El rezago vive en el tópico, no en la RAM.
- **Offset después de procesar.** Commit manual; falla transitoria → reintento con backoff
  sin avanzar; mensaje inservible (JSON, versión, regla de negocio) → se registra y se avanza.
- **12 particiones** (mayor que `maxReplicas: 6` de `ms-siniestros`). `ms-parametrico` es
  dueño del tópico y el único con `CreateTopic` sobre él.
- **El consumidor no bloquea el arranque** de `ms-siniestros`: sin MSK solo se detiene el
  canal paramétrico; el aviso asistido sigue disponible.

## Alcance

- `apps/backend/ms-siniestros/`: casos de uso, repositorio SQL, puerto y stub de desembolso,
  ruta, consumidor (`app/infrastructure/consumidor_telemetria.py`, `msk.py`), config, main,
  dependencias y locks, pruebas.
- `apps/backend/ms-parametrico/` (nuevo): servicio completo, pruebas, Dockerfile, locks.
- `apps/backend/docker-compose.yml`, `apps/backend/observability/prometheus.yml`.
- `infra/k8s/values/{ms-parametrico,ms-siniestros}.yaml`,
  `infra/k8s/platform/crear-topico-telemetria.yaml`,
  `infra/terraform/modules/irsa_aplicacion/main.tf`, `.github/workflows/deploy.yml`.

## Despliegue

**Terraform primero, merge después.** Runbook, plan esperado y verificación en
[`docs/despliegue-telemetria-parametrica.md`](../../docs/despliegue-telemetria-parametrica.md).

## Fuera de alcance (pendiente)

- El umbral, la vigencia y el monto siguen llegando del emisor (ahora un proveedor
  autenticado). La versión objetivo los resuelve contra una proyección local de pólizas
  paramétricas alimentada por `PolizaEmitida`.
- Un evento afecta a una póliza. El reparto de un evento a N pólizas exige idempotencia
  `(evento_externo_id, poliza_id)`.
- Autenticación del proveedor por firma HMAC o mTLS; hoy es `clientId`/`clientSecret`.
- Exposición de `ms-parametrico` por ALB + API Gateway (ruta dedicada). Hoy es interno.
- DLQ productiva para mensajes descartados (hoy solo log + métrica `descartado`).
- Desembolso real vía `ColaPagos` → `ms-pagos`.
- Medición de EC-ESC-03/04 a escala (1.000.000 de eventos en 10 min): no se corrió.
- El pago **asistido** (`avisos.py::_ejecutar_pago`) también desembolsa antes del commit.
- `test_pagos_recibidos_le_pertenecen_al_dueno` (integración) falla también en `develop`:
  asyncpg no acepta una migración de varias sentencias en un `execute`.

## Criterios de aceptación

- [x] Rama `feature/telemetria-parametrica` desde `origin/develop` (`e540e213`).
- [x] Una falla a mitad de la cadena no deja nada persistido y la reingesta paga una vez.
- [x] Solo se desembolsa un pago confirmado; un desembolso fallido deja `enrutado` y la
      reingesta lo cierra en `pagado`.
- [x] 10 ingestas concurrentes del mismo `evento_id` en PostgreSQL: 1 siniestro, 1 pago.
- [x] Solo `operador` ingiere por `POST /v1/eventos-parametricos` (asesor y cliente: 403).
- [x] `ms-parametrico`: 202 con ack, 401 sin credenciales, 422 con esquema inválido, 429 y
      503 con `Retry-After`.
- [x] Consumidor: offset después de procesar, reintento transitorio, descarte de inservibles.
- [x] E2E local: proveedor → ApiTelemetria → Kafka → ms-siniestros → pago.
- [x] `terraform validate` del módulo IRSA.

## Evidencia

Pruebas:

- `ms-siniestros` unitarias: 158 passed, 1 skipped (antes: 135).
- `ms-siniestros` integración contra PostgreSQL 16: 10 passed; 1 failed preexistente (arriba).
- `ms-parametrico`: 19 passed, cobertura 88 % (el resto es el cliente real de Kafka, cubierto
  por el E2E).
- `terraform validate` (hashicorp/terraform:1.9.8) sobre `modules/irsa_aplicacion`: válido.

E2E con `docker compose -p solventa-telemetria-e2e up -d --build ms-parametrico ms-siniestros`:

- `crear-topico-telemetria`: `topico_creado=TopicoTelemetria`, 12 particiones.
- Mismo reporte de vuelo enviado dos veces: 202 y 202; en BD `vuelos:E2E-1` `pagado`,
  `count(pago_parametrico) = 1`, traza `recibido<topico-telemetria -> … -> pagado`.
- Clima bajo umbral: `clima:E2E-2` `decidido`, `umbral_no_alcanzado`, sin pago.
- Sin credenciales: 401. Esquema inválido: 422 `esquema_proveedor_invalido`.
- Consumidor detenido + 30 eventos: 30 × 202. Al reiniciar, lag 0 y en BD 30 siniestros,
  24 pagados y 6 sin pago: coincide con el oráculo (retraso `100 + 3i ≥ 120` ⇔ `i ≥ 7`).
- Kafka detenido: `503` + `Retry-After: 2`; `ms-siniestros /health/ready` 200. Kafka de
  vuelta: el reintento entra con 202 y `vuelos:CAIDA-1` queda `pagado` con un solo pago.
