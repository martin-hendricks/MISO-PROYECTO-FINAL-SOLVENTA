# ms-polizas

Ciclo de vida de la póliza: alta, cambios, renovación, cancelación.

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-LAT-05/06, EC-MOD-01/02

## HU cubiertas

- **HU-16 · Emitir póliza (SOLV-109).** Emite la póliza de una oferta aceptada con número único, vigencia de un año, coberturas y estado `VIGENTE`, y la deja consultable de inmediato.

## API

| Método | Ruta | Respuesta |
| --- | --- | --- |
| `POST` | `/v1/polizas` | `201` póliza emitida · `200` ya existía para esa oferta (reintento) · `422` suscripción no aceptada, cobro no exitoso o coberturas inválidas · `503` ms-suscripcion o ms-pagos no disponible |
| `GET` | `/v1/polizas/{poliza_id}` | `200` póliza · `404` no existe |

Cuerpo de `POST /v1/polizas`:

```json
{
  "solicitud_id": "uuid",
  "oferta_id": "uuid",
  "usuario_id": "uuid",
  "token_pago_confirmado": "uuid del pago aprobado en ms-pagos",
  "coberturas": [{ "nombre": "Responsabilidad civil", "suma_asegurada": "50000000.00", "deducible": "0" }]
}
```

## Reglas

- **Precondiciones.** Solo se emite si la suscripción de `solicitud_id` está `ACEPTADA` en ms-suscripcion (HU-13) y `token_pago_confirmado` es un cobro `APROBADO` de la misma oferta en ms-pagos (HU-15). El token es el `pago_id` del cobro: el `TokenPagoConfirmado` de `ComandoEmisionDTO`.
- **Idempotencia.** Una sola póliza por `oferta_id` (`uq_poliza_oferta`). Un reintento devuelve la póliza existente, sin volver a validar ni consumir número.
- **Número.** `POL-<año>-<secuencia>`, tomado de `ms_polizas.poliza_numero_seq`. La secuencia nunca retrocede, así el número no se reutiliza ni tras una cancelación (HU-61).
- **Evento.** `PolizaEmitida` va al outbox en la misma transacción que la póliza.

## Dependencias

| Variable | Uso |
| --- | --- |
| `DATABASE_URL` | PostgreSQL, esquema `ms_polizas` |
| `MS_SUSCRIPCION_URL` | Consulta `GET /v1/suscripciones/{solicitud_id}` (puerto `VerificadorSuscripcion`) |
| `MS_PAGOS_URL` | Consulta `GET /v1/pagos/{pago_id}` (puerto `VerificadorCobro`) |
| `TIMEOUT_DEPENDENCIAS` | Timeout en segundos de las llamadas a otros servicios (por defecto `2.0`) |

## Pruebas

```bash
pip install -e ".[test]"
pytest -m "not integration and not contract" --allow-hosts=127.0.0.1,::1 --cov
```
