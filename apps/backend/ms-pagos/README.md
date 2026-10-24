# ms-pagos

Débito de primas, conciliación y desembolso de indemnizaciones. Cola de pagos idempotente.

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-DISP-03/04/05 (disponibilidad ≥ 99.99%, idempotencia, cero pérdida de transacciones confirmadas)

## HU cubiertas

- **HU-15 · Cobro de prima, stub idempotente (SOLV-108).** Cobra la prima de una oferta con suscripción aceptada contra una pasarela simulada. El `pago_id` de un cobro `APROBADO` es el `TokenPagoConfirmado` que ms-polizas exige para emitir (HU-16).

## API

| Método | Ruta | Respuesta |
| --- | --- | --- |
| `POST` | `/v1/pagos/primas` | `201` cobro registrado (`APROBADO` o `RECHAZADO`) · `200` reintento: devuelve el cobro original · `422` suscripción no aceptada o monto inválido · `503` ms-suscripcion no disponible |
| `GET` | `/v1/pagos/{pago_id}` | `200` resultado del cobro · `404` no existe |

Cuerpo de `POST /v1/pagos/primas`:

```json
{
  "solicitud_id": "uuid",
  "oferta_id": "uuid",
  "usuario_id": "uuid",
  "monto": "250000.00",
  "token_medio_pago": "tok_visa"
}
```

## Reglas

- **Idempotencia.** La clave es `cobro-prima:{oferta_id}`: se deriva de la operación, no del intento. La garantiza `uq_transaccion_idempotency`. Un reintento no llama a la pasarela y devuelve el resultado original, aun si fue un rechazo.
- **Stub.** `PasarelaStub` no se integra con ningún proveedor. El token `tok_rechazo` produce `RECHAZADO`; cualquier otro, `APROBADO`.
- **Persistencia.** El resultado (éxito o fallo) queda en `pago` + `transaccion_pasarela`, y `PagoPrimaRegistrado` va al outbox en la misma transacción. El pago de la prima se referencia por `oferta_id`, porque la póliza aún no existe al cobrar.

## Dependencias

| Variable | Uso |
| --- | --- |
| `DATABASE_URL` | PostgreSQL, esquema `ms_pagos` |
| `MS_SUSCRIPCION_URL` | Consulta `GET /v1/suscripciones/{solicitud_id}` (puerto `VerificadorSuscripcion`) |
| `TIMEOUT_DEPENDENCIAS` | Timeout en segundos de las llamadas a otros servicios (por defecto `2.0`) |

## Pruebas

```bash
pip install -e ".[test]"
pytest -m "not integration and not contract" --allow-hosts=127.0.0.1,::1 --cov
```
