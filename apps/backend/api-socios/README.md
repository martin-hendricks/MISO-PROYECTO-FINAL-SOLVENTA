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

**Pendiente:** la credencial de socio (`requiere_rol("socio")` de `solventa_seguridad`) entra con HU-76; hasta entonces el router `/v1` no exige token.

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

Después, `pytest -m contract` en `ms-cotizacion` verifica que el núcleo cumple ese pacto. El paso de CI que corre ambos es de HU-88.

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
