# ms-polizas

Ciclo de vida de la póliza: alta, cambios, renovación, cancelación.

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-LAT-05/06, EC-MOD-01/02

## HU cubiertas

- **HU-16 · Emitir póliza (SOLV-109).** Emite la póliza de una oferta aceptada con número único, vigencia de un año, coberturas y estado `VIGENTE`, y la deja consultable de inmediato.
- **HU-17 · Firma electrónica stub (SOLV-110).** Antes de emitir se firma la oferta con un stub que responde ok / no. Cada resultado queda guardado con su marca de tiempo; si la firma falla, no se emite la póliza.

## API

| Método | Ruta | Respuesta |
| --- | --- | --- |
| `POST` | `/v1/polizas` | `201` póliza emitida · `200` ya existía para esa oferta (reintento) · `422` suscripción no aceptada, cobro no exitoso, firma no exitosa o coberturas inválidas · `503` ms-suscripcion o ms-pagos no disponible |
| `GET` | `/v1/polizas/firmas/{oferta_id}` | `200` última constancia de firma de la oferta · `404` la oferta no tiene constancia |
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
- **Firma (HU-17).** Se firma después de validar suscripción y cobro, y solo si no existe ya una póliza para la oferta, así que un reintento no vuelve a firmar. Cada resultado se guarda en `constancia_firma`:
  - **ok:** la constancia y la póliza se guardan en la misma transacción. La póliza guarda el hash en `firma_hash` y lo devuelve como `hash_firma_legal`.
  - **no:** la constancia se guarda sola con su motivo y la emisión responde `422 firma_no_exitosa`.

  `GET /v1/polizas/firmas/{oferta_id}` devuelve el resultado más reciente (`OK` / `NO`, motivo, hash, `firmada_en`). Lee del writer, no de la réplica, para que el flujo no reciba un estado atrasado.
- **Adaptador de firma.** El caso de uso depende del puerto `FirmaElectronica` (`app/ports/firma.py`). Hoy lo implementa `FirmaStub` (`app/infrastructure/firma.py`), sin prestador, sin PDF y sin validez legal. Cambiarlo por un prestador real no cambia el contrato del núcleo.
- **Pendiente de arquitectura.** La hoja de la semana 8 saca la firma del camino crítico (táctica *limitar la respuesta a los eventos*). HU-17 exige lo contrario: si la firma falla, no se emite. Por eso aquí la firma es síncrona. Hoy cabe en el p95 ≤ 1,5 s porque el stub no tiene latencia; con un prestador real hay que volver a evaluar esta decisión.

## Dependencias

| Variable | Uso |
| --- | --- |
| `DATABASE_URL` | PostgreSQL, esquema `ms_polizas` |
| `MS_SUSCRIPCION_URL` | Consulta `GET /v1/suscripciones/{solicitud_id}` (puerto `VerificadorSuscripcion`) |
| `MS_PAGOS_URL` | Consulta `GET /v1/pagos/{pago_id}` (puerto `VerificadorCobro`) |
| `FIRMA_STUB_RESULTADO` | Resultado del stub de firma: `ok` (por defecto) o `no` |
| `TIMEOUT_DEPENDENCIAS` | Timeout en segundos de las llamadas a otros servicios (por defecto `2.0`) |

## Pruebas

```bash
pip install -e ".[test]"
pytest -m "not integration and not contract" --allow-hosts=127.0.0.1,::1 --cov
```
