# ms-suscripcion

Decide aceptar/rechazar/ajustar riesgo, de forma automática o asistida (underwriting).

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-LAT-05/06 (suscripción y emisión, p95 ≤ 1.5s, p99 ≤ 3s), EC-MOD-04

## Qué resuelve (HU-13 · SOLV-106)

Decisión **automática** de suscripción, sin underwriter: acepta o rechaza el riesgo de una solicitud con un motivo y una marca de tiempo. Esa decisión es la fuente que leen el cobro (HU-15), la emisión (HU-16) y las vistas de rechazo de los canales.

- La regla es **dato**: tabla `regla_suscripcion` (`db/02_ms_suscripcion_regla.sql`). Un `score <= score_maximo` se acepta y cualquier otro se rechaza. Para cambiarla basta un `UPDATE`, sin desplegar. Solo puede haber una regla vigente.
- La decisión es **determinista** e **idempotente por `solicitud_id`**: si se reintenta, se devuelve la decisión ya persistida.
- Cada decisión publica `SuscripcionDecidida` por outbox, en la misma transacción.
- El `score` llega en la petición mientras `ms-perfilamiento` no esté implementado.

| Método | Ruta | Respuesta |
| --- | --- | --- |
| `POST` | `/v1/suscripciones` `{solicitud_id, perfil_id, score}` | `201` decisión nueva · `200` reintento · `422` score inválido · `503` sin regla vigente |
| `GET` | `/v1/suscripciones/{solicitud_id}` | `200` decisión · `404` sin decisión |

No llama a otros servicios, así que no usa variables `MS_*_URL`.

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
docker build --target test -t ms-suscripcion:test . && docker run --rm ms-suscripcion:test
```

## Ejecutar con Docker (HU-71)

```bash
docker compose up --build          # servicio en :8080 + PostgreSQL 16 con el DDL de db/
```

La imagen fija el runtime (`python:3.12.7-slim-bookworm`, nunca `latest`) y corre con un usuario sin privilegios (uid 1000). El puerto 8080 y el uid son los que espera el chart `infra/k8s/charts/microservicio`; con `uvicorn` local sin Docker el servicio sigue en :8000.

Las dependencias de la imagen se instalan con `requirements.lock` como *constraints*: dos construcciones del mismo commit instalan las mismas versiones. Si cambia `pyproject.toml`, se regenera el lock (sin Docker):

```bash
uv pip compile pyproject.toml --extra test --python-version 3.12.7 --python-platform x86_64-unknown-linux-gnu -o requirements.lock
```

## Despliegue

Imagen `runtime` del `Dockerfile` hacia EKS (vista de despliegue §1.1.3). El DDL oficial del servicio está en `db/schema/NN_ms_<nombre>.sql` del repo y se aplica sobre su propia instancia o schema RDS.
