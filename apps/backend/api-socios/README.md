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

### Autenticación de socios externos

Cada socio (empresa aliada que integra cotización embebida, no una persona con cuenta en
Solventa) tiene una API key propia enviada en la cabecera `X-Socio-Api-Key`. Es
autenticación servicio-a-servicio, sin flujo de login. Solventa guarda solo el hash SHA-256
de cada clave y lo compara en tiempo constante (`app/seguridad.py`).

| Caso | Respuesta |
| --- | --- |
| Falta la cabecera o la clave no corresponde a ningún socio | `401` |
| La clave es válida pero el socio no tiene el alcance de la ruta | `403` |

| Alcance | Rutas |
| --- | --- |
| `catalogo:leer` | `GET /v1/catalogo`, `GET /v1/catalogo/{codigo}` |
| `originaciones:escribir` | `POST /v1/originaciones-hipotecarias` |

#### Registro de socios (`SOCIOS`)

Lista JSON; cada entrada es un socio. El servicio no arranca si una entrada es inválida
(`socio_id` no UUID, hash que no sea SHA-256 hexadecimal en minúsculas, alcance desconocido,
`socio_id` o hash repetidos).

```json
[
  {
    "socio_id": "1ebbe2fc-d8b1-4046-af76-b92bacec52ff",
    "nombre": "Aliado local",
    "alcances": ["catalogo:leer", "originaciones:escribir"],
    "api_keys_sha256": ["48bc804a45c5da3acc09c94bb86c9cc3e5bb8443eeef076dc574f09a2baed13c"]
  }
]
```

#### Alta de un socio (sin cambiar código)

1. Generar la clave: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
2. Calcular su huella: `python -c "import hashlib,sys; print(hashlib.sha256(sys.argv[1].encode()).hexdigest())" <clave>`.
3. Agregar la entrada a `SOCIOS` con un `socio_id` nuevo (`python -c "import uuid; print(uuid.uuid4())"`), su nombre, sus alcances y la huella.
4. Reiniciar `api-socios` para que lea el registro.
5. Entregar la clave al socio por un canal seguro. Solventa no conserva la clave en claro.

#### Rotación de la clave

1. Agregar la huella de la clave nueva a `api_keys_sha256` del socio, sin quitar la anterior, y reiniciar.
2. El socio cambia a la clave nueva; mientras tanto ambas son válidas.
3. Quitar la huella anterior y reiniciar.

Para revocar a un socio, se quita su entrada y se reinicia.

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
| `MS_IDENTIDAD_URL` | `http://localhost:8010` | `ms-identidad`: resuelve el documento del cliente |
| `MS_PERFILAMIENTO_URL` | `http://localhost:8004` | `ms-perfilamiento`: registra la originación |
| `SOLVENTA_TOKEN_SECRET` | vacío | Firma el token de servicio `socio`; es el mismo secreto que bff-web y ms-identidad. En k8s llega por `ExternalSecret` desde `solventa-minimo-bff-web-token` |
| `SOCIO_SERVICIO_UID` | `00000000-0000-0000-0000-00000000500c` | `uid` del token de servicio |
| `SOCIOS` | `[]` | Registro JSON de socios con sus alcances y las huellas SHA-256 de sus API keys (ver "Registro de socios"). Vacío: toda llamada a `/v1` responde 401 |
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
