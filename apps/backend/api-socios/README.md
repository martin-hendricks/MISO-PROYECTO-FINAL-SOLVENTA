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
Solventa) tiene una API key propia, estática, enviada en la cabecera `X-Socio-Api-Key`. No es
un JWT de sesión: no hay flujo de login para un socio externo, es autenticación
servicio-a-servicio. Todos los endpoints de `/v1` la exigen (`app/seguridad.py`,
`exigir_api_key_socio`) y responden `401 {"codigo": ...}` si falta la cabecera o la clave no
coincide con ninguna configurada (`SOCIOS_API_KEYS`, ver tabla de variables abajo).

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
| `SOCIOS_API_KEYS` | vacío | Credenciales de socios que llaman a `/v1` (cabecera `X-Socio-Api-Key`), formato `socio_id:api_key` separados por coma. Ej. `aliado-banco:clave-secreta,aliado-retail:otra-clave`. Formato de prueba/local; en un ambiente real cada socio tendría su propia fila en un almacén de credenciales |
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
