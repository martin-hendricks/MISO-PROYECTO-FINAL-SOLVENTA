# ms-cotizacion

Calcula prima en tiempo real combinando reglas actuariales, riesgo y señales de Open Finance. Motor de rating.

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-LAT-01/02 (p95 ≤ 250ms, p99 ≤ 500ms), EC-ESC-01/02 (50k cotizaciones/min)

## API · HU-3 Recibir solicitud de cotización ([SOLV-96](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-96))

`POST /v1/cotizaciones`

```json
{
  "producto": "PROTECCION_DISPOSITIVO",
  "datosRiesgo": { "valorDispositivo": 2400000, "marca": "Pixel", "masDe12Meses": false }
}
```

`201` · oferta en firme con su `cotizacionId`:

```json
{
  "cotizacionId": "6f1c2b0e-0c1d-4c7e-9a51-3f3d7f6b9a10",
  "producto": "PROTECCION_DISPOSITIVO",
  "estado": "oferta_vigente",
  "prima": "89000.00",
  "moneda": "COP",
  "coberturas": [{ "codigo": "ROBO", "nombre": "Robo", "limite": "8000000" }],
  "venceEn": "2026-10-07T12:00:00Z"
}
```

`422` · error de negocio tipificado, sin `cotizacionId`. Nombra el campo y, si aplica, su rango:

```json
{
  "codigo": "dato_riesgo_fuera_de_rango",
  "mensaje": "'valorDispositivo' fuera de rango: debe estar entre 300000 y 8000000",
  "campo": "valorDispositivo",
  "rangoValido": { "tipo": "entero", "min": 300000, "max": 8000000 }
}
```

| `codigo` | Cuándo |
| --- | --- |
| `producto_inexistente` | El producto no está en el catálogo |
| `dato_riesgo_faltante` | Falta un dato del riesgo del producto |
| `dato_riesgo_tipo_invalido` | El dato no es del tipo esperado |
| `dato_riesgo_fuera_de_rango` | El dato está fuera del rango válido |
| `dato_riesgo_no_reconocido` | Llega un dato que el producto no define |
| `solicitud_invalida` | El cuerpo no tiene la forma del contrato |

### Flujo

```
POST ─► Catalogo (HU-1) ─► valida datosRiesgo ─► CalculadoraPrima (HU-4) ─► FactorRiesgo (HU-5)
                                                 ─► Cotizacion.ofertar (HU-6) ─► RepositorioCotizaciones (HU-7)
```

Cada colaborador es un puerto (`app/ports/cotizacion.py`) y su implementación se elige en `app/dependencies.py`.

### Estado de la primera iteración

| Puerto | Implementación actual | Pendiente |
| --- | --- | --- |
| `Catalogo` | `CatalogoEnMemoria`: un ramo provisional, **Protección de dispositivo** | HU-1 ([SOLV-94](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-94)): ramo oficial (Jira dice SOAT motocicleta, la wiki Protección de dispositivo), coberturas, límites y rangos |
| `CalculadoraPrima` | `PrimaFijaStub` (89.000 COP) | HU-4 ([SOLV-97](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-97)) |
| `FuenteFactorRiesgo` | `FactorRiesgoNeutroStub` (1,0) | HU-5 ([SOLV-98](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-98)) |
| `RepositorioCotizaciones` | En memoria del proceso, purga lo vencido | Almacén compartido entre réplicas para HU-7 (PostgreSQL `ms_cotizacion` o Redis con TTL) |
| Contrato Pact | `tests/contract/` marcado `skip` | HU-88 ([SOLV-181](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-181)) |

Esta iteración no usa base de datos: se retiró la infraestructura SQL del arquetipo. El DDL oficial (`db/schema/04_ms_cotizacion.sql`) exige `usuario_id`, `socio_id` y `consentimiento_id`, que la HU-3 aún no recibe.

## Desarrollo

**Requisitos:** Python 3.12+ (o solo Docker).

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[test]"
uvicorn app.main:app --reload                       # http://localhost:8000/docs
```

| Variable | Default | Uso |
| --- | --- | --- |
| `VIGENCIA_OFERTA_MINUTOS` | `1440` | Vigencia de la oferta en firme (valor de referencia, lo fija HU-6) |
| `LOG_LEVEL` | `INFO` | |

## Pruebas (HU-85)

```bash
pytest -m "not integration and not contract" --cov           # unitarias: sin BD ni red
```

En CI las unitarias corren con el workflow de backend del PR #10 (`backend-unit-tests.yml`), con cobertura y reporte JUnit.

Las mismas pruebas dentro de la imagen base (HU-71):

```bash
docker build --target test -t ms-cotizacion:test . && docker run --rm ms-cotizacion:test
```

## Ejecutar con Docker (HU-71)

```bash
docker compose up --build          # servicio en :8000
```

La imagen fija el runtime (`python:3.12.7-slim-bookworm`, nunca `latest`) y corre con un usuario sin privilegios.

## Despliegue

Imagen `runtime` del `Dockerfile` hacia EKS (vista de despliegue §1.1.3). El DDL oficial del servicio está en `db/schema/04_ms_cotizacion.sql` del repo y se aplica sobre su propia instancia o schema RDS.
