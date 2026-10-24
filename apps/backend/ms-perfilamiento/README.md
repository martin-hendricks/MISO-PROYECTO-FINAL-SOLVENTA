# ms-perfilamiento

Enriquece el perfil de riesgo del cliente con datos de Open Data y Open Finance para ofertas competitivas y precio personalizado (caso insignia: vida hipotecario).

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-LAT-03/04 (p95 ≤ 400ms, p99 ≤ 800ms), EC-LAT-09 (degradación ante dependencia lenta)

## Alcance (HU-53, HU-54, HU-55, HU-56)

- **HU-53 — Consentimiento de perfilamiento:** otorgar/revocar consentimiento de perfilamiento, **distinto e independiente** de cualquier otro consentimiento de datos general (otra HU, otro microservicio). Sin consentimiento vigente no se invoca ningún adaptador externo.
- **HU-54 — Adaptadores stub Open Finance / Open Data:** dos puertos (`Protocol`) sustituibles, cada uno con su stub determinista. El núcleo nunca conoce el esquema de un proveedor real.
- **HU-55 — Perfil y oferta explicable:** Solventa arma un `Perfil` propio a partir de los atributos de los adaptadores y calcula una `Oferta` con precio + factores internos en lenguaje de negocio, en el mismo flujo.
- **HU-56 — Degradar perfilamiento lento:** si un adaptador excede su timeout o falla, se sustituye por un valor de respaldo marcando `degradado=True`; la oferta se entrega igual y la originación nunca se cancela.

## Estructura (hexagonal)

```
app/
├── main.py              crear_app(): lifespan, manejo de errores de dominio → HTTP
├── config.py            pydantic-settings: timeouts, valores de respaldo y pesos de la fórmula de oferta
├── dependencies.py      raíz de composición: qué implementación cumple cada puerto
├── observabilidad.py    /health, /metrics (Prometheus), X-Correlation-Id
├── api/v1/              POST /v1/consentimientos, GET/DELETE /v1/consentimientos/{cliente_id}, POST /v1/ofertas-hipotecario
├── domain/               Consentimiento, AtributoPerfil, Perfil, Oferta, FactorInterno + fórmula de precio
├── application/         casos de uso: otorgar/revocar/consultar consentimiento, perfilar_y_ofertar
├── ports/               persistencia.py (repos + UoW) y adaptadores.py (AdaptadorOpenFinance/AdaptadorOpenData)
└── infrastructure/      SQLAlchemy 2 async + transactional outbox + stubs de los adaptadores
db/01_ms_perfilamiento.sql   DDL del almacén (desarrollo local)
tests/                   PyTest sin red ni BD (dobles de los puertos) + integración marcada
```

La dependencia va **hacia adentro**: `api → application → domain`, e `infrastructure` implementa `ports`. El dominio no importa nada de FastAPI, SQLAlchemy ni asyncio.

## Atributos propios de Solventa (HU-54)

Ninguno es el payload real de un proveedor: son atributos **inventados por Solventa** para fines del proyecto académico.

| Adaptador | Atributo | Significado (negocio) |
| --- | --- | --- |
| Open Finance | `nivel_ingresos_estimado` | Nivel de ingresos estimado del cliente, normalizado en [0,1] |
| Open Finance | `score_comportamiento` | Score de comportamiento financiero, normalizado en [0,1] |
| Open Data | `zona_riesgo` | Riesgo asociado a la zona geográfica del cliente, normalizado en [0,1] |
| Open Data | `antiguedad_documento` | Antigüedad relativa del documento de identidad, normalizada en [0,1] |

El stub de cada adaptador (`app/infrastructure/adaptadores.py`) deriva un valor **determinista** por `cliente_id` (hash estable, sin red ni aleatoriedad real), para que las pruebas sean reproducibles.

## Fórmula de oferta (HU-55)

Determinista y simple, **no es un modelo de scoring real**:

```
ajuste = 1 + Σ (peso_atributo * valor_atributo)
precio = tarifa_base * ajuste        # redondeado a 2 decimales, mínimo simbólico > 0
```

Pesos y tarifa base por defecto (configurables en `app/config.py` / `.env`):

| Atributo | Peso | Impacto en la prima |
| --- | --- | --- |
| `nivel_ingresos_estimado` | `-0.08` | `reduce_prima` |
| `score_comportamiento` | `-0.15` | `reduce_prima` |
| `zona_riesgo` | `+0.20` | `aumenta_prima` |
| `antiguedad_documento` | `-0.05` | `reduce_prima` |

`tarifa_base = 50000` (COP). Cada atributo usado produce un `FactorInterno` `{"factor": "<atributo>", "impacto": "reduce_prima"|"aumenta_prima", "peso": <peso>}` que acompaña la oferta — nunca se expone el valor crudo de ningún proveedor, solo el nombre del atributo propio de Solventa y su efecto cualitativo.

## Degradación (HU-56)

Cada adaptador tiene su propio timeout (`timeout_open_finance_ms`, `timeout_open_data_ms`, 400ms por defecto) aplicado con `asyncio.wait_for` en `app/application/casos_uso.py`. Si expira o el adaptador lanza cualquier excepción, el atributo correspondiente se sustituye por su valor de respaldo (constante configurable) y se marca `degradado=True` para ese atributo; la `Oferta` resultante expone `degradado=true` si al menos uno de sus atributos vino del respaldo. La oferta degradada sigue siendo válida y se persiste junto con el snapshot completo de insumos (`snapshot_atributos`), para que la decisión de precio sea 100% reconstruible aunque las reglas cambien después.

Valores de respaldo por defecto: `nivel_ingresos_estimado=1.0`, `score_comportamiento=0.5`, `zona_riesgo=0.5`, `antiguedad_documento=1.0`.

<!-- desarrollo -->

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
| `TIMEOUT_OPEN_FINANCE_MS` / `TIMEOUT_OPEN_DATA_MS` | `400` | Timeout por adaptador (HU-54/HU-56) |
| `RESPALDO_*` | ver `.env.example` | Valor de respaldo por atributo (HU-56) |
| `TARIFA_BASE`, `PESO_*` | ver `.env.example` | Fórmula de oferta (HU-55) |

## Pruebas

```bash
pytest -m "not integration and not contract" --cov           # unitarias: sin BD ni red
```

Integración contra un PostgreSQL 16 con el DDL de `db/` aplicado:

```bash
docker compose up -d db                                      # PostgreSQL local con el DDL de db/
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/solventa pytest -m integration
```

`tests/dobles.py` incluye `AdaptadorConfigurable`, una variante de los adaptadores stub que se puede configurar con `latencia_ms` o `fallar=True` para ejercer en tests el camino de `asyncio.wait_for` expirando (HU-56), sin depender de red real.

Las mismas pruebas dentro de la imagen base:

```bash
docker build --target test -t ms-perfilamiento:test . && docker run --rm ms-perfilamiento:test
```

## Ejecutar con Docker

```bash
docker compose up --build          # servicio en :8080 + PostgreSQL 16 con el DDL de db/
```

La imagen fija el runtime (`python:3.12.7-slim-bookworm`, nunca `latest`) y corre con un usuario sin privilegios (uid 1000). El puerto 8080 es el que espera el chart `infra/k8s/charts/microservicio`; con `uvicorn` local sin Docker el servicio sigue en :8000.

Las dependencias de la imagen se instalan con `requirements.lock` como *constraints*. Si cambia `pyproject.toml`, se regenera el lock (sin Docker):

```bash
uv pip compile pyproject.toml --extra test --python-version 3.12.7 --python-platform x86_64-unknown-linux-gnu -o requirements.lock
```

## Despliegue

Imagen `runtime` del `Dockerfile` hacia EKS. El DDL oficial del servicio está en `db/schema/05_ms_perfilamiento.sql` del repo y se aplica sobre su propia instancia o schema RDS.
