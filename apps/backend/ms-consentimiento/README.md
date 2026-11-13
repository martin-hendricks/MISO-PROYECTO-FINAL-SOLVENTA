# ms-consentimiento

Otorgamiento y revocación de consentimiento de datos personales bajo habeas data (Ley 1581) y Finanzas Abiertas.

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-SEG-03 (revocación efectiva ≤ 5 min, propagada vía eventos)

## Alcance real de esta implementación: STUB explícito

Esta implementación **NO** es la integración legal/de cumplimiento completa que sugiere el ASR EC-SEG-03. Es un servicio interno simple que registra el hecho de otorgamiento/revocación de consentimiento de habeas data y expone ese dato al resto de la plataforma (hoy, `ms-identidad`). Concretamente:

- **No propaga la revocación por eventos.** No hay outbox ni `EventoDominio` en este servicio: revocar solo actualiza la fila en `ms_consentimiento.consentimiento`. El ASR EC-SEG-03 pide que la revocación sea efectiva y propagada en ≤5 minutos a todo el sistema vía eventos — eso **no está implementado**. Cualquier consumidor que necesite enterarse de una revocación debe **consultar el endpoint de lectura** (`GET /v1/consentimientos/{cliente_id}`), no escuchar un evento.
- **No versiona la política legal.** No existe `version_politica`, snapshot del texto aceptado, ni distinción entre finalidades de tratamiento. El modelo de dominio solo guarda `otorgado_en`/`revocado_en` para un único tipo fijo (`habeas_data`).
- **Es consumo servicio-a-servicio, sin JWT de usuario final.** No valida ningún token de cliente: se asume que quien lo llama (otros microservicios del backend, como `ms-identidad`) ya resolvió la autenticación en el borde.

Ver el docstring de `Consentimiento` en `app/domain/modelos.py` para el mismo aviso en el código, y `odd/tasks/ms-consentimiento-habeas-data.md` para el detalle de alcance de esta tarea y lo que queda deliberadamente fuera.

## Contrato HTTP

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/v1/consentimientos` | Otorga consentimiento (`{"cliente_id": "..."}`). Idempotente: 201 si crea uno nuevo, 200 si ya había uno vigente. |
| `GET` | `/v1/consentimientos/{cliente_id}` | Consentimiento vigente del cliente. 404 si nunca otorgó uno o si el último fue revocado. |
| `DELETE` | `/v1/consentimientos/{cliente_id}` | Revoca el consentimiento vigente. 404 si no había ninguno vigente. |

Las tres rutas devuelven `{"id", "cliente_id", "otorgado_en", "revocado_en", "vigente"}`.

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
docker build --target test -t ms-consentimiento:test . && docker run --rm ms-consentimiento:test
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
