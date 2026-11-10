# ms-identidad

Onboarding, verificación (KYC/AML) y emisión de identidad. Emisor de JWT (validado en los BFF, no en el emisor).

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-SEG-07 (bloqueo de ataques ≤ 1s), autorización por rol (RBAC)

Pendiente de implementación.

## Verificación KYC (HU-88)

El alta (`POST /v1/usuarios`) consulta el puerto `VerificadorKYC` (`app/ports/kyc.py`) antes de crear la cuenta. Hoy no hay proveedor real: el adaptador es el doble `VerificadorKYCStub` (`app/infrastructure/kyc.py`), y cambiarlo por uno real no toca `application/` ni `domain/`.

| Respuesta del KYC | Alta |
| --- | --- |
| Aprueba | 201, la cuenta se crea |
| Rechaza el documento | 422 `identidad_no_verificada`, no se crea la cuenta |
| No responde | 503 `dependencia_no_disponible`, no se crea la cuenta |

Por defecto el doble aprueba todo documento, así que el alta se comporta igual que sin KYC. En el ambiente de integración se configura por entorno:

| Variable | Default | Efecto |
| --- | --- | --- |
| `DOBLE_KYC_DOCUMENTOS_RECHAZADOS` | vacío | Documentos separados por comas que el KYC rechaza, p. ej. `0000000000,123` |
| `DOBLE_KYC_FALLAR` | `false` | El KYC no responde |
| `DOBLE_KYC_LATENCIA_MS` | `0` | Demora de cada verificación |

```bash
DOBLE_KYC_DOCUMENTOS_RECHAZADOS=0000000000 docker compose up -d ms-identidad   # desde apps/backend
```

`bff-web` traduce el 422 a un 422 con el mensaje del núcleo (no a "la cuenta ya existe") y el 503 a `servicio_no_disponible`.

## Cuentas de cliente (operador y asesor)

| Método | Ruta | Quién | Efecto |
| --- | --- | --- | --- |
| `GET` | `/v1/usuarios?rol=cliente&estado=&q=&ids=&pagina=` | operador, asesor | Solo `rol=cliente`. Página de 20, o `len(ids)` si hay ids (máximo 50). `q` de menos de 2 caracteres y un `rol` distinto de `cliente` responden 422 |
| `PATCH` | `/v1/usuarios/{id}` | operador | `nombre`, `apellidos` (1–80) y `email` en minúsculas. 404 si no es cliente. 409 si el correo ya existe |
| `POST` | `/v1/usuarios/{id}/estado` | operador | `{estado: ACTIVO\|INACTIVO}`. El mismo estado no escribe evento. Un cambio escribe `UsuarioInactivado` o `UsuarioReactivado` (`{usuario_id, ocurrido_en}`) en `ms_identidad.outbox_evento`, en la misma transacción |

Una cuenta `INACTIVO` no puede autenticarse. Reactivarla no vuelve a encender los dispositivos push.
