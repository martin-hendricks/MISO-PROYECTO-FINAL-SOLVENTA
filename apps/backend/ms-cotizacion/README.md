# ms-cotizacion

Calcula prima en tiempo real combinando reglas actuariales, riesgo y señales de Open Finance. Motor de rating.

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-LAT-01/02 (p95 ≤ 250ms, p99 ≤ 500ms), EC-ESC-01/02 (50k cotizaciones/min)

## Historias cubiertas

| HU | Jira | Qué resuelve |
| --- | --- | --- |
| HU-1 · Catálogo mínimo (1 ramo) | [SOLV-94](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-94) | Catálogo persistido con el ramo **SOAT motocicleta**: coberturas fijas, sus límites (en SMLDV), la moneda y el rango válido de cada dato del riesgo. Se consulta por código con `casos_uso.consultar_producto`; un código inexistente lanza `ProductoNoEncontrado` (`producto_no_encontrado`, 404). |
| HU-2 · Publicar catálogo al socio | [SOLV-95](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-95) | Consulta interna `GET /v1/productos` y `GET /v1/productos/{codigo}` que consume `:APISocios`. Verifica el pacto de `api-socios` (`tests/contract/`). |
| HU-3 · Recibir solicitud de cotización | [SOLV-96](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-96) | `POST /v1/cotizaciones`: valida producto y datos de riesgo contra el catálogo de HU-1, devuelve `cotizacionId` único con idempotencia por `Idempotency-Key`. |
| HU-4 · Calcular prima con reglas | [SOLV-97](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-97) | Motor de rating determinista (`regla_rating`, datos no código): prima neta, gastos de expedición y moneda, con redondeo estable. |
| HU-5 · Combinar factor de riesgo (stub) | [SOLV-98](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-98) | Adaptador sustituible `AdaptadorPerfilRiesgo` con timeout (EC-LAT-08) y valor de respaldo auditable si falla o llega tarde. |
| HU-6 · Devolver oferta en firme | [SOLV-99](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-99) | La misma llamada de HU-3 devuelve la oferta completa (`prima`, `moneda`, `venceEn`, desglose, origen del factor). |
| HU-7 · Reconsultar oferta por id | [SOLV-100](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-100) | `GET /v1/cotizaciones/{cotizacionId}`: lectura pura, sin recálculo; marca ofertas vencidas con su precio original. |

### Catálogo de productos (HU-1)

- **Persistido** en `ms_cotizacion.producto`, `cobertura_producto` y `dato_riesgo_producto` (`db/05_ms_cotizacion_catalogo.sql`, extensión aditiva del DDL oficial `db/schema/04_ms_cotizacion.sql`, con la semilla de SOAT motocicleta).
- **Solo lectura en ejecución:** `CatalogoSQL` lo carga una vez al arrancar (si está vacío, el servicio no arranca) y lo sirve desde memoria, sin un viaje a la BD por cotización (EC-LAT-01). El puerto `CatalogoProductos` solo expone `obtener` y `listar`; no hay alta ni edición desde ningún canal.
- **Un ramo nuevo es dato, no código** (EC-MOD-01): se agregan filas al catálogo y el contrato no cambia.
- La consulta HTTP es interna (HU-2): el socio llega por `api-socios`, nunca directo.

### Cotización embebida (HU-3 a HU-7)

- `POST /v1/cotizaciones` orquesta en una sola transacción: valida contra el catálogo (HU-1), calcula la prima base (`regla_rating`, HU-4), combina el factor de riesgo con degradación auditable (HU-5) y emite la oferta en firme (HU-6).
- `GET /v1/cotizaciones/{cotizacionId}` (HU-7) es lectura pura: nunca invoca el motor de rating ni el adaptador de perfil.
- Extiende aditivamente el DDL oficial vía `db/02_ms_cotizacion_solicitud.sql` (idempotencia + datos de riesgo), `db/03_ms_cotizacion_rating.sql` (desglose de prima) y `db/04_ms_cotizacion_factor_riesgo.sql` (origen del factor de riesgo).

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

Contrato Pact (HU-2): verifica que el núcleo cumple el pacto que publica `api-socios` en `api-socios/pacts/`:

```bash
pip install -e ".[test,contract]"
pytest -m contract
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

Imagen `runtime` del `Dockerfile` hacia EKS (vista de despliegue §1.1.3). El DDL oficial del servicio está en `db/schema/04_ms_cotizacion.sql` del repo; el schema `ms_cotizacion` vive en la instancia `rds_compartida` que provisiona Terraform (`infra/terraform/environments/minimo`). Sobre ella se aplican, en orden, los archivos de `db/` de este servicio (`02_` a `05_` extienden aditivamente el DDL oficial con idempotencia, rating, factor de riesgo y catálogo).
