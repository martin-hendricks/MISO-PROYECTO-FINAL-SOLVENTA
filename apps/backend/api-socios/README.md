# api-socios

Expone catálogo y cotización a canales de terceros (socios de distribución embebida) vía API. Autenticación fuerte, autorización por alcance, cuotas y rotación de credenciales.

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-SEG-07, EC-ESC-05 (aislamiento de carga entre socios)

## Historias cubiertas

| HU | Jira | Qué resuelve |
| --- | --- | --- |
| HU-2 · Publicar catálogo al socio | [SOLV-95](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-95) | Endpoint versionado de solo lectura con el catálogo de HU-1: producto, coberturas, límites, moneda y rango de cada dato del riesgo. Contrato propio de Solventa (camelCase), verificado con Pact contra `ms-cotizacion`. |

### Contrato `/v1` (HU-2)

| Método | Ruta | Respuesta |
| --- | --- | --- |
| `GET` | `/v1/catalogo` | `{"productos": [Producto]}` |
| `GET` | `/v1/catalogo/{codigo}` | `Producto`, o `404 {"codigo": "no_encontrado"}` |

`Producto` = `codigo`, `nombre`, `moneda`, `coberturas[]` (`codigo`, `nombre`, `limite: {valor, unidad}`) y `datosRiesgo[]` (`nombre`, `tipo` = `rango` con `minimo`/`maximo`, o `valores` con `valores[]`). No expone campos internos del núcleo. Un campo nuevo entra siempre como opcional; quitar o renombrar uno es `/v2`.

### Originación hipotecaria (R5 · vida hipotecario)

| Método | Ruta | Cuerpo | Respuesta |
| --- | --- | --- | --- |
| `POST` | `/v1/originaciones-hipotecarias` | `{"tipoDocumento", "numeroDocumento", "valor", "plazoMeses"}` | `201 {"estado": "pendiente", "valor", "plazoMeses"}` |

El banco aliado envía el crédito de un cliente que ya tiene cuenta en Solventa. `api-socios` resuelve el documento en `ms-identidad` (`GET /v1/usuarios/documento`, con un token de servicio de rol `socio`) y registra la originación en `ms-perfilamiento` con `origen = socio`. El cliente ve la card **Vida hipotecario** en Inicio con esos valores, que no puede modificar, y solo autoriza el perfilamiento y acepta.

| Caso | Respuesta |
| --- | --- |
| Documento sin cuenta en Solventa | `404 {"codigo": "cliente_no_registrado"}` |
| Datos inválidos o campos de más | `422` sin llamar al núcleo |
| `valor`/plazo que rechaza `ms-perfilamiento` | El `422` del núcleo con su `codigo` |
| `ms-identidad` o `ms-perfilamiento` caídos, o el token rechazado | `503 {"codigo": "servicio_no_disponible"}` |

### Cotización embebida (recorrido 1)

| Método | Ruta | Cuerpo | Respuesta |
| --- | --- | --- | --- |
| `POST` | `/v1/cotizaciones` (cabecera `Idempotency-Key`, 8 a 91 caracteres) | `{"tipoDocumento", "numeroDocumento", "producto", "datosRiesgo"}` | `201 {"cotizacionId", "estado", "producto", "prima", "primaNeta", "gastosExpedicion", "moneda", "venceEn", "vencida", "consentimientoPendiente"}`; `200` al reintentar con la misma clave |
| `GET` | `/v1/cotizaciones/{cotizacionId}` | — | `200` con la misma vista, sin `consentimientoPendiente` |

El socio cotiza cualquier producto del catálogo para un cliente que ya tiene cuenta en Solventa. `api-socios` resuelve el documento en `ms-identidad`, consulta el consentimiento de perfil vigente en `ms-perfilamiento` y cotiza en `ms-cotizacion` con `canal = socio` y el `socio_id` de la API key; el socio no puede enviarlo. Si el cliente no tiene consentimiento vigente, la cotización se crea igual con `consentimientoPendiente: true`: el cliente recibe un aviso en mobile para autorizarlo, y el consentimiento se exige al aceptar. La `Idempotency-Key` se antepone con el `socio_id`, así que la clave de un socio nunca choca con la de otro.

| Caso | Respuesta |
| --- | --- |
| Documento sin cuenta en Solventa | `404 {"codigo": "cliente_no_registrado"}` |
| Falta `Idempotency-Key`, datos inválidos o campos de más (p. ej. `socioId`) | `422` sin llamar al núcleo |
| Datos de riesgo que rechaza `ms-cotizacion` | El `422` del núcleo con su `codigo` |
| Cotización de otro socio o inexistente | `404` |
| Un servicio del núcleo caído | `503 {"codigo": "servicio_no_disponible"}` |

### Autenticación de socios externos

Cada socio (empresa aliada que integra cotización embebida, no una persona con cuenta en
Solventa) tiene una API key propia enviada en la cabecera `X-Socio-Api-Key`. Es
autenticación servicio-a-servicio, sin flujo de login. `api-socios` calcula la huella SHA-256 de la clave
y resuelve el socio en `ms-identidad` (`POST /v1/socios/resolucion`, con un token de servicio de rol
`socio`); la clave en claro nunca sale de `api-socios` (`app/seguridad.py`, `app/registro_socios.py`).

| Caso | Respuesta |
| --- | --- |
| Falta la cabecera o la clave no corresponde a ningún socio activo | `401` |
| La clave es válida pero el socio no tiene el alcance de la ruta | `403` |
| `ms-identidad` no responde | `503 {"codigo": "servicio_no_disponible"}` |

| Alcance | Rutas |
| --- | --- |
| `catalogo:leer` | `GET /v1/catalogo`, `GET /v1/catalogo/{codigo}` |
| `originaciones:escribir` | `POST /v1/originaciones-hipotecarias` |
| `cotizaciones:escribir` | `POST /v1/cotizaciones` |
| `cotizaciones:leer` | `GET /v1/cotizaciones/{cotizacionId}` |

#### Registro de socios (`ms-identidad`)

El operador administra los socios en `ms-identidad` (ver su README, sección "Socios de distribución"):
alta con sus alcances (la API key se entrega una sola vez), rotación de clave, revocación de una clave
y revocación del socio. Ninguno de esos pasos cambia código ni reinicia `api-socios`.

El socio resuelto se guarda en memoria durante `CACHE_SOCIOS_S` segundos (30 por defecto): es el
tiempo máximo que tarda en hacer efecto una revocación. Una clave desconocida no se guarda, así que
una clave recién emitida sirve de inmediato.

## Desarrollo

**Requisitos:** Python 3.12+ (o solo Docker).

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[test]"
uvicorn app.main:app --reload --port 8080          # http://localhost:8080/docs
```

| Variable | Default | Uso |
| --- | --- | --- |
| `MS_COTIZACION_URL` | `http://localhost:8000` | `ms-cotizacion`: fuente del catálogo |
| `MS_IDENTIDAD_URL` | `http://localhost:8010` | `ms-identidad`: resuelve el socio por la huella de su API key y el documento del cliente |
| `MS_PERFILAMIENTO_URL` | `http://localhost:8004` | `ms-perfilamiento`: registra la originación |
| `SOLVENTA_TOKEN_SECRET` | vacío | Firma el token de servicio `socio`; es el mismo secreto que bff-web y ms-identidad. En k8s llega por `ExternalSecret` desde `solventa-minimo-bff-web-token` |
| `CACHE_SOCIOS_S` | `30` | Segundos que se reutiliza un socio resuelto en `ms-identidad`; tope de demora de una revocación |
| `TIMEOUT_NUCLEO_S` | `1.0` | Timeout por llamada al núcleo |
| `TIMEOUT_OPCIONAL_S` | `0.3` | Corte de fuentes opcionales en vistas agregadas |

## Pruebas (HU-85)

```bash
pytest -m "not integration and not contract" --cov
```

El núcleo se simula con `httpx.MockTransport`: sin red.

Contrato Pact con `ms-cotizacion` (este servicio es el consumidor; genera `pacts/api-socios-ms-cotizacion.json`, que se versiona en el repo):

```bash
pip install -e ".[test,contract]"
pytest -m contract
```

Después, `pytest -m contract` en `ms-cotizacion` verifica que el núcleo cumple ese pacto. En CI ambos corren en ese orden en el workflow `backend-contract-tests.yml` (HU-88).

En la imagen (contexto `apps/backend`):

```bash
docker build -f Dockerfile --target test -t api-socios:test .. && docker run --rm api-socios:test
```

## Ejecutar con Docker (HU-71)

```bash
docker compose up --build          # api-socios :8080 + ms-cotizacion + PostgreSQL con el DDL de ms-cotizacion/db
```

El contexto de build es `apps/backend`, para que las imágenes de los BFF puedan incluir código compartido del backend.

## Despliegue

Imagen `runtime` detrás del `:ApiGateway` (ALB + WAF) hacia EKS (§1.1.3). El canal solo conoce la URL del gateway.
