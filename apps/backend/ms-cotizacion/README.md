# ms-cotizacion

Calcula prima en tiempo real combinando reglas actuariales, riesgo y señales de Open Finance. Motor de rating.

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-LAT-01/02 (p95 ≤ 250ms, p99 ≤ 500ms), EC-ESC-01/02 (50k cotizaciones/min)

## Historias cubiertas

| HU | Jira | Qué resuelve |
| --- | --- | --- |
| HU-1 · Catálogo mínimo (1 ramo) | [SOLV-94](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-94) | Catálogo persistido con el ramo **SOAT motocicleta**: coberturas fijas, sus límites (en SMLDV), la moneda y el rango válido de cada dato del riesgo. Se consulta por código con `casos_uso.consultar_producto`; un código inexistente lanza `ProductoNoEncontrado` (`producto_no_encontrado`, 404). |

### Catálogo de productos (HU-1)

- **Persistido** en `ms_cotizacion.producto`, `cobertura_producto` y `dato_riesgo_producto` (`db/05_ms_cotizacion_catalogo.sql`, extensión aditiva del DDL oficial `db/schema/04_ms_cotizacion.sql`, con la semilla de SOAT motocicleta).
- **Solo lectura en ejecución:** `CatalogoSQL` lo carga una vez al arrancar (si está vacío, el servicio no arranca) y lo sirve desde memoria, sin un viaje a la BD por cotización (EC-LAT-01). El puerto `CatalogoProductos` solo expone `obtener`; no hay alta ni edición desde ningún canal.
- **Un ramo nuevo es dato, no código** (EC-MOD-01): se agregan filas al catálogo y el contrato no cambia.
- Sin endpoint HTTP propio: la publicación del catálogo es HU-2 (SOLV-95).

## Desarrollo

**Requisitos:** Python 3.12+ (o solo Docker).

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[test]"
uvicorn app.main:app --reload                       # http://localhost:8000/docs
```

| Variable | Default | Uso |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/solventa` | Almacén propio del servicio |
| `DB_POOL_SIZE` | `10` | Conexiones por réplica |
| `LOG_LEVEL` | `INFO` | |

## Pruebas (HU-85)

```bash
pytest -m "not integration and not contract" --cov           # unitarias: sin BD ni red
```

Integración contra un PostgreSQL 16 con el DDL de `db/` aplicado:

```bash
docker compose up -d db                                      # PostgreSQL local con el DDL de db/
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/solventa pytest -m integration
```

En CI las unitarias corren con el workflow de backend del PR #10 (`backend-unit-tests.yml`), con cobertura y reporte JUnit. Las pruebas marcadas `integration` por ahora se corren en local.

Las mismas pruebas dentro de la imagen base (HU-71):

```bash
docker build --target test -t ms-cotizacion:test . && docker run --rm ms-cotizacion:test
```

## Ejecutar con Docker (HU-71)

```bash
docker compose up --build          # servicio en :8000 + PostgreSQL 16 con el DDL de db/
```

La imagen fija el runtime (`python:3.12.7-slim-bookworm`, nunca `latest`) y corre con un usuario sin privilegios.

## Despliegue

Imagen `runtime` del `Dockerfile` hacia EKS (vista de despliegue §1.1.3). El DDL oficial del servicio está en `db/schema/04_ms_cotizacion.sql` del repo; el schema `ms_cotizacion` vive en la instancia `rds_compartida` que provisiona Terraform (`infra/terraform/environments/minimo`). Sobre ella se aplican, en orden, los archivos de `db/` de este servicio (el `05_*` trae el catálogo y su semilla).
