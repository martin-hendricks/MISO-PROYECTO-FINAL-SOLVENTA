# ms-parametrico · ApiTelemetria

Puerta de entrada de la telemetría paramétrica. Recibe eventos de proveedores externos (vuelos, clima), los traduce al evento canónico de Solventa y los publica en `TopicoTelemetria`. No tiene base de datos ni evalúa: el consumidor es `ms-siniestros` (decisión D5, opción B).

**Stack:** Python 3.12 + FastAPI + aiokafka
**ASRs:** EC-ESC-03 (absorber ≥ 1.000.000 de eventos en 10 min con contrapresión) · EC-ESC-04 (procesamiento exactamente una vez, del lado del consumidor) · EC-MOD-05 (sustituir un proveedor sin tocar el núcleo)

```
Proveedor ──► :ApiTelemetria ──► :AdaptadorTelemetria ──► TopicoTelemetria ──► :MotorParametrico (ms-siniestros)
              POST /v1/telemetria/{proveedor}/eventos      (12 particiones,        evalúa umbral y paga
              202 · 429 · 503 + Retry-After                 key = evento_id)
```

## Contrato

`POST /v1/telemetria/{proveedor}/eventos`, con las cabeceras `X-Telemetria-Cliente` y `X-Telemetria-Secreto`.

| Respuesta | Significado | Qué hace el proveedor |
| --- | --- | --- |
| `202` `{"evento_id": "vuelos:R-1", "aceptado": true}` | El tópico confirmó la escritura (`acks=all`). Evaluación y pago ocurren después | Nada. Reenviar es seguro: el consumidor deduplica por `evento_id` |
| `401` | Credenciales ausentes o inválidas | Corregir credenciales |
| `404` | Proveedor no registrado | — |
| `422` `esquema_proveedor_invalido` | La carga no cumple el esquema de ese proveedor (campos desconocidos incluidos) | Corregir la carga |
| `429` `contrapresion` + `Retry-After` | La réplica llegó a `MAX_PUBLICACIONES_EN_VUELO` | Reintentar después |
| `503` `topico_no_disponible` + `Retry-After` | El broker no confirmó a tiempo; el evento **no** quedó aceptado | Reintentar después |

Proveedores simulados (`app/adaptadores/`):

| Proveedor | Carga | `evento_id` | `valor` |
| --- | --- | --- | --- |
| `vuelos` | `reporte_id`, `vuelo`, `fecha`, `retraso_minutos`, `reportado_en`, `cobertura` | `vuelos:<reporte_id>` | minutos de retraso |
| `clima` | `medicion_id`, `estacion`, `precipitacion_mm`, `medido_en`, `cobertura` | `clima:<medicion_id>` | mm de precipitación |

`cobertura` = `{umbral, monto, vigente?, poliza_id?, poliza_numero?, usuario_id?}`. El evento canónico que viaja por el tópico está en `app/domain/evento.py` (`version: 1`). Para agregar un proveedor se escribe un módulo en `app/adaptadores/` y se registra en `ADAPTADORES`; ni la ruta ni el consumidor cambian.

## Por qué así

- **202 en vez de 201.** EC-ESC-03 pide *recibir y persistir* el pico; la evaluación es EC-ESC-04 y es asíncrona. La ingesta no toca ninguna BD, así que su costo por evento es una escritura en Kafka.
- **Contrapresión explícita.** Con el cupo de publicaciones en vuelo lleno, la réplica responde 429 en lugar de encolar peticiones en memoria. El rezago lo guarda el tópico, que tiene retención durable, no la RAM del pod.
- **key = `evento_id`.** Todas las entregas de un evento van a la misma partición y el consumidor las procesa en orden.

## Fuera de alcance

- El umbral y el monto llegan en `cobertura`, desde el proveedor autenticado. La versión objetivo los resuelve contra una proyección local de pólizas paramétricas.
- Reparto de un evento a N pólizas. Firma HMAC o mTLS por proveedor. DLQ productiva.
- Exposición por ALB + API Gateway: hoy el servicio es interno al clúster.
- Medición a escala de EC-ESC-03/04.

Detalle y evidencia: `odd/tasks/telemetria-parametrica.md`.

## Desarrollo

```bash
uv venv --python 3.12 .venv && uv pip install -e ".[test]"
pytest -m "not integration and not contract" --allow-hosts=127.0.0.1,::1 --cov
uvicorn app.main:app --reload        # sin MSK_BOOTSTRAP_BROKERS los eventos quedan en memoria
```

| Variable | Default | Uso |
| --- | --- | --- |
| `MSK_BOOTSTRAP_BROKERS` | vacío | Vacío = publicador en memoria (solo desarrollo) |
| `MSK_TOPIC` | `TopicoTelemetria` | |
| `MSK_AUTH_MECHANISM` | `AWS_MSK_IAM` | `PLAINTEXT` contra el Kafka local |
| `TELEMETRIA_CLIENT_ID` / `TELEMETRIA_CLIENT_SECRET` | vacío | En EKS llegan como `clientId`/`clientSecret` del secreto `telemetria_iot`. Sin ellas responde 500 |
| `MAX_PUBLICACIONES_EN_VUELO` | `500` | Cupo por réplica antes de responder 429 |
| `TIMEOUT_PUBLICACION_SEGUNDOS` | `5` | Sin ack en ese tiempo → 503 |
| `REINTENTAR_DESPUES_SEGUNDOS` | `2` | Valor de `Retry-After` |

### De punta a punta en local

```bash
cd apps/backend
docker compose up -d --build ms-parametrico ms-siniestros     # levanta kafka, crea el tópico, db y s3

curl -s localhost:8013/v1/telemetria/vuelos/eventos \
  -H 'Content-Type: application/json' \
  -H 'X-Telemetria-Cliente: proveedor-demo' \
  -H 'X-Telemetria-Secreto: clave-local-de-pruebas-no-usar-en-produccion' \
  -d '{"reporte_id":"R-1","vuelo":"AV234","fecha":"2026-11-20","retraso_minutos":190,
       "reportado_en":"2026-11-20T14:00:00Z","cobertura":{"umbral":"120","monto":"180000.00"}}'
```

El siniestro `vuelos:R-1` aparece en `ms_siniestros.siniestro` en estado `pagado`.

## Despliegue

`infra/k8s/values/ms-parametrico.yaml`. El rol IRSA (`modules/irsa_aplicacion`) permite producir en `TopicoTelemetria` y crearlo. `deploy.yml` crea el tópico una sola vez con el Job `infra/k8s/platform/crear-topico-telemetria.yaml` (`python -m app.crear_topico`, 12 particiones). Hay que aplicar Terraform **antes** del primer deploy, porque sin el rol el Job falla. Runbook: [`docs/despliegue-telemetria-parametrica.md`](../../../docs/despliegue-telemetria-parametrica.md).
