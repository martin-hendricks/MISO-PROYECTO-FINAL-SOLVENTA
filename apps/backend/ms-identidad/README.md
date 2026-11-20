# ms-identidad

Onboarding, verificación (KYC/AML) y emisión de identidad. Emisor de JWT (validado en los BFF, no en el emisor).

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-SEG-07 (bloqueo de ataques ≤ 1s), autorización por rol (RBAC)

Pendiente de implementación.

## Búsqueda por documento (originación hipotecaria por socios)

`GET /v1/usuarios/documento?tipo_documento=CC&numero_documento=1012345678` devuelve solo `{"usuario_id": …}`. Lo pueden llamar los roles `socio`, `asesor` y `operador`; un `cliente` recibe `403`, sin token `401` y un documento sin cuenta `404`. Normaliza igual que el alta (tipo en mayúsculas, número sin espacios).

El rol `socio` lo usa `api-socios` con su token de servicio. Con ese rol no se puede leer ni modificar la cuenta completa (`GET /v1/usuarios/{id}` responde `403`).

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

## Socios de distribución

Registro de los socios que entran por `api-socios` (HA-29: el alta no cambia código ni despliega la plataforma). Solventa guarda solo la huella SHA-256 de cada API key; la clave en claro se entrega una sola vez, en la respuesta que la emite.

| Método | Ruta | Quién | Efecto |
| --- | --- | --- | --- |
| `POST` | `/v1/socios` | operador, asesor | `{nombre, alcances}` → `201` con `socio_id`, `credencial_id` y `api_key`. Alcances: `catalogo:leer`, `originaciones:escribir`, `cotizaciones:escribir`, `cotizaciones:leer`; al menos uno. Campos de más → 422 |
| `GET` | `/v1/socios` | operador, asesor | Socios con su estado y sus credenciales (`credencial_id`, `creada_en`, `revocada_en`), sin claves ni huellas |
| `POST` | `/v1/socios/{id}/credenciales` | operador, asesor | Rotación: `201` con una `api_key` nueva; las anteriores siguen válidas. 409 si el socio está revocado |
| `DELETE` | `/v1/socios/{id}/credenciales/{credencial_id}` | operador, asesor | Revoca esa clave. `204`; 404 si la credencial no es de ese socio |
| `POST` | `/v1/socios/{id}/revocacion` | operador, asesor | Revoca el socio y todas sus claves. Idempotente |
| `POST` | `/v1/socios/resolucion` | `api-socios` (token de rol `socio` con `sub = api-socios`) | `{huella_sha256}` → `{socio_id, nombre, alcances}`. 404 si la huella no existe, está revocada o el socio está revocado |

Tablas `ms_identidad.socio` y `ms_identidad.credencial_socio` (`db/07_ms_identidad_socios.sql`).

`db/08_ms_identidad_socio_default.sql` siembra el socio por defecto `Aliado local` (`socio_id` `1ebbe2fc-d8b1-4046-af76-b92bacec52ff`) con los cuatro alcances y la API key `solventa123` (solo se guarda su huella). Es una clave conocida: en un ambiente real el operador debe rotarla y revocar la original.
