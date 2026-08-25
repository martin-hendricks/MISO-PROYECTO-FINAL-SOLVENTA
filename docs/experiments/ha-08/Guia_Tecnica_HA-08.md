# Guía técnica de implementación — Experimento HA-08

**Caso de estudio:** Solventa — plataforma insurtech
**Curso:** MISW4501 — Arquitectura de Software
**Historia de arquitectura:** HA-08 | **ASR:** EC-LAT-11 (Latencia, p95 ≤ 150 ms)
**Versión:** 1.0

> **Documento base:** el propósito, la hipótesis de diseño, los puntos de sensibilidad, los estilos y tácticas, el diseño experimental, los criterios de aceptación y las amenazas a la validez están en `Diseno_Experimento_HA-08.md`. Este documento cubre exclusivamente **cómo montar y ejecutar** el experimento.

---

## Tabla de contenido

1. [Resumen operativo](#1-resumen-operativo)
2. [Arquitectura del montaje](#2-arquitectura-del-montaje)
3. [Estructura del proyecto](#3-estructura-del-proyecto)
4. [Configuración Docker](#4-configuración-docker)
5. [Modelo de datos](#5-modelo-de-datos)
6. [Contrato de eventos de dominio](#6-contrato-de-eventos-de-dominio)
7. [Implementación de la API y los brazos](#7-implementación-de-la-api-y-los-brazos)
8. [Proyector y simulador](#8-proyector-y-simulador)
9. [Generación del dataset](#9-generación-del-dataset)
10. [Perfil de carga](#10-perfil-de-carga)
11. [Protocolo de ejecución](#11-protocolo-de-ejecución)
12. [Métricas recolectadas](#12-métricas-recolectadas)
13. [Verificaciones de sanidad](#13-verificaciones-de-sanidad)
14. [Solución de problemas](#14-solución-de-problemas)
15. [Anexo — Comandos de referencia](#15-anexo--comandos-de-referencia)

---

## 1. Resumen operativo

El montaje implementa tres estrategias de lectura sobre el mismo binario, seleccionables por la variable de entorno `READ_STRATEGY`:

| Brazo | Estrategia | Camino de lectura |
|---|---|---|
| **A** | Línea base | API → PostgreSQL `siniestros_w` → 5 joins + agregaciones |
| **B** | CQRS | API → PostgreSQL `siniestros_r` → `SELECT payload WHERE siniestro_id = $1` |
| **C** | CQRS + caché | API → Redis (acierto) o → proyección + `SETEX` (fallo) |
| **C'** | C sin re-serialización | Igual a C, devolviendo los bytes cacheados sin revalidar |

Ejecutar los cuatro brazos sobre el mismo binario elimina la diferencia de código de aplicación como variable confusora.

**Dos requisitos del escenario EC-LAT-11 condicionan el montaje:**

- *"el estado del siniestro cambia por eventos del proceso de evaluación"* — la medición se hace con la proyección **bajo actualización activa**. El simulador debe estar corriendo durante toda la ventana de medición.
- *"producción en condiciones regulares"* — el veredicto se emite sobre el escalón de operación regular, no sobre el punto de saturación.

---

## 2. Arquitectura del montaje

```
                     ┌─────────────────────┐
                     │  k6 (carga lectura) │
                     └──────────┬──────────┘
                                │ HTTP
                     ┌──────────▼──────────┐
                     │  FastAPI / Uvicorn  │
                     │ READ_STRATEGY=A|B|C │
                     └──┬────────┬───────┬─┘
              brazo A   │        │       │  brazo C
          ┌─────────────┘        │       └─────────────┐
          │             brazo B  │                     │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
│ PostgreSQL        │  │ PostgreSQL        │  │ Redis 7           │
│ siniestros_w      │  │ siniestros_r      │  │ cache-aside       │
│ (normalizado)     │  │ (materializado)   │  │ TTL 30s           │
└─────────▲─────────┘  └─────────▲─────────┘  └─────────▲─────────┘
          │                      │                      │
          │                      └──────────┬───────────┘
          │                        upsert + invalidación
          │                      ┌──────────┴───────────┐
          │                      │  Proyector (worker)  │
          │                      │  aiokafka consumer   │
          │                      └──────────▲───────────┘
          │                                 │
          │                      ┌──────────┴───────────┐
          │                      │ Redpanda (Kafka API) │
          │                      │ topic: siniestros.ev │
          │                      └──────────▲───────────┘
          │                                 │
          └──────────────┬──────────────────┘
                ┌────────┴────────────────┐
                │ Simulador de evaluación │
                │ escribe + publica       │
                └─────────────────────────┘

  Observabilidad: Prometheus ← API, proyector, k6 (remote-write) → Grafana
```

---

## 3. Estructura del proyecto

```
experiments/ha-08-cqrs-read-model/          # raíz del experimento en el monorepo
├── docker-compose.yml
├── .env.example                 # plantilla versionada (.env real ignorado)
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # app FastAPI, lifespan, endpoint
│       ├── config.py            # settings por env
│       ├── db.py                # pool asyncpg
│       ├── cache.py             # cliente redis.asyncio
│       ├── metrics.py           # histogramas prometheus_client
│       ├── models.py            # response_model Pydantic
│       └── strategies/
│           ├── arm_a.py         # joins sobre siniestros_w
│           ├── arm_b.py         # SELECT sobre siniestros_r
│           └── arm_c.py         # cache-aside sobre arm_b
├── projector/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── projector.py
├── simulator/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── simulator.py
├── db/
│   └── init/
│       ├── 01_schema_write.sql
│       ├── 02_schema_read.sql
│       ├── 03_seed.sql
│       └── 04_backfill_projection.sql
├── load/k6/read_estado.js
├── observability/
│   ├── prometheus.yml
│   └── grafana/provisioning/
├── scripts/
│   ├── run_experiment.sh
│   ├── verify_parity.sh
│   └── collect_results.sh
└── results/raw/
```

> **Ubicación en el monorepo.** El experimento vive en
> `experiments/ha-08-cqrs-read-model/` dentro del repositorio
> `MISO-PROYECTO-FINAL-SOLVENTA`, y esa carpeta es la raíz del árbol anterior.
> Todas las rutas de esta guía (`./api`, `./db/init`, `./scripts`, …) son
> relativas a ella: **todos los comandos `docker compose` y los scripts de
> `scripts/` deben ejecutarse con esa carpeta como directorio de trabajo.**
>
> ```bash
> cd experiments/ha-08-cqrs-read-model
> cp .env.example .env      # el .env real no se versiona
> docker compose up -d
> ```
>
> Esta guía y el documento de diseño residen en `docs/experiments/ha-08/`.

---

## 4. Configuración Docker

### `.env`

```bash
# --- Estrategia de lectura (A | B | C | C_PRIME) ---
READ_STRATEGY=A

# --- Identificación de la corrida ---
RUN_ID=r1

# --- PostgreSQL ---
POSTGRES_USER=solventa
POSTGRES_PASSWORD=solventa
POSTGRES_DB=solventa
PG_SHARED_BUFFERS=256MB
PG_EFFECTIVE_CACHE_SIZE=512MB

# --- API ---
UVICORN_WORKERS=2
DB_POOL_MIN=10
DB_POOL_MAX=10
CACHE_TTL_SECONDS=30

# --- Simulador ---
EVENTS_PER_SECOND=5

# --- Dataset ---
TOTAL_SINIESTROS=1000000
HOT_SET_SIZE=10000
```

### `docker-compose.yml`

```yaml
name: solventa-ha08

x-limits-small: &limits-small
  deploy:
    resources:
      limits:
        cpus: "0.5"
        memory: 512M

services:

  postgres:
    image: postgres:16-alpine
    container_name: ha08-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    command: >
      postgres
      -c shared_buffers=${PG_SHARED_BUFFERS}
      -c effective_cache_size=${PG_EFFECTIVE_CACHE_SIZE}
      -c max_connections=100
      -c random_page_cost=1.1
      -c track_io_timing=on
      -c log_min_duration_statement=500
    volumes:
      - ./db/init:/docker-entrypoint-initdb.d:ro
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 20
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G

  redis:
    image: redis:7-alpine
    container_name: ha08-redis
    command: >
      redis-server
      --save ""
      --appendonly no
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
    <<: *limits-small

  redpanda:
    image: redpandadata/redpanda:v24.2.7
    container_name: ha08-redpanda
    command:
      - redpanda
      - start
      - --mode=dev-container
      - --smp=1
      - --overprovisioned
      - --node-id=0
      - --kafka-addr=PLAINTEXT://0.0.0.0:9092
      - --advertise-kafka-addr=PLAINTEXT://redpanda:9092
    ports:
      - "9092:9092"
    healthcheck:
      test: ["CMD-SHELL", "rpk cluster health | grep -q 'Healthy:.*true'"]
      interval: 10s
      timeout: 5s
      retries: 20
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 1G

  api:
    build: ./api
    container_name: ha08-api
    environment:
      READ_STRATEGY: ${READ_STRATEGY}
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      DB_POOL_MIN: ${DB_POOL_MIN}
      DB_POOL_MAX: ${DB_POOL_MAX}
      CACHE_TTL_SECONDS: ${CACHE_TTL_SECONDS}
      UVICORN_WORKERS: ${UVICORN_WORKERS}
    ports:
      - "8000:8000"
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request;urllib.request.urlopen('http://localhost:8000/health')\""]
      interval: 5s
      timeout: 3s
      retries: 20
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G

  projector:
    build: ./projector
    container_name: ha08-projector
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      KAFKA_BOOTSTRAP: redpanda:9092
      TOPIC: siniestros.eventos
      CONSUMER_GROUP: proyector-estado
    depends_on:
      postgres: { condition: service_healthy }
      redpanda: { condition: service_healthy }
      redis: { condition: service_healthy }
    ports:
      - "8001:8001"     # /metrics
    <<: *limits-small

  simulator:
    build: ./simulator
    container_name: ha08-simulator
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      KAFKA_BOOTSTRAP: redpanda:9092
      TOPIC: siniestros.eventos
      EVENTS_PER_SECOND: ${EVENTS_PER_SECOND}
      HOT_SET_SIZE: ${HOT_SET_SIZE}
    depends_on:
      postgres: { condition: service_healthy }
      redpanda: { condition: service_healthy }
    <<: *limits-small

  prometheus:
    image: prom/prometheus:v2.54.1
    container_name: ha08-prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --web.enable-remote-write-receiver
      - --storage.tsdb.retention.time=7d
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - promdata:/prometheus
    ports:
      - "9090:9090"
    <<: *limits-small

  grafana:
    image: grafana/grafana:11.2.0
    container_name: ha08-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_ORG_ROLE: Viewer
    volumes:
      - ./observability/grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "3000:3000"
    <<: *limits-small

  k6:
    image: grafana/k6:0.53.0
    container_name: ha08-k6
    profiles: ["load"]
    environment:
      K6_PROMETHEUS_RW_SERVER_URL: http://prometheus:9090/api/v1/write
      K6_PROMETHEUS_RW_TREND_STATS: "p(50),p(95),p(99),avg,max"
      BASE_URL: http://api:8000
      ARM: ${READ_STRATEGY}
      RUN_ID: ${RUN_ID}
    volumes:
      - ./load/k6:/scripts:ro
      - ./results/raw:/results
    entrypoint:
      - k6
      - run
      - --out
      - experimental-prometheus-rw
      - --summary-export=/results/summary_${READ_STRATEGY}_${RUN_ID}.json
      - /scripts/read_estado.js
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M

volumes:
  pgdata:
  promdata:
```

> **Sobre los límites de recursos.** `deploy.resources.limits` es honrado por Docker Compose V2 fuera de Swarm. La suma de límites (≈9 CPU) excede lo disponible en una máquina de 4–8 núcleos: es intencional, porque los servicios no alcanzan su pico simultáneamente, pero obliga a verificar con `docker stats` que ningún componente de infraestructura esté saturado durante la corrida.

### `api/Dockerfile`

```dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 \
     --workers ${UVICORN_WORKERS:-2} --loop uvloop --http httptools --no-access-log"]
```

### `api/requirements.txt`

```
fastapi==0.115.*
uvicorn[standard]==0.30.*
asyncpg==0.29.*
redis==5.0.*
orjson==3.10.*
pydantic==2.9.*
pydantic-settings==2.5.*
prometheus-client==0.21.*
```

### `observability/prometheus.yml`

```yaml
global:
  scrape_interval: 5s
  evaluation_interval: 15s

scrape_configs:
  - job_name: api
    static_configs:
      - targets: ["api:8000"]
    metrics_path: /metrics

  - job_name: projector
    static_configs:
      - targets: ["projector:8001"]
    metrics_path: /metrics
```

---

## 5. Modelo de datos

### `db/init/01_schema_write.sql` — modelo transaccional

```sql
CREATE SCHEMA IF NOT EXISTS siniestros_w;

CREATE TABLE siniestros_w.poliza (
    id              BIGINT PRIMARY KEY,
    cliente_id      BIGINT        NOT NULL,
    numero          TEXT          NOT NULL,
    producto        TEXT          NOT NULL,
    estado          TEXT          NOT NULL,
    suma_asegurada  NUMERIC(14,2) NOT NULL,
    vigencia_desde  DATE          NOT NULL,
    vigencia_hasta  DATE          NOT NULL
);

CREATE TABLE siniestros_w.siniestro (
    id                BIGINT PRIMARY KEY,
    poliza_id         BIGINT      NOT NULL REFERENCES siniestros_w.poliza(id),
    cliente_id        BIGINT      NOT NULL,
    numero            TEXT        NOT NULL,
    estado            TEXT        NOT NULL,
    causa             TEXT        NOT NULL,
    monto_estimado    NUMERIC(14,2),
    monto_aprobado    NUMERIC(14,2),
    fecha_ocurrencia  TIMESTAMPTZ NOT NULL,
    fecha_aviso       TIMESTAMPTZ NOT NULL,
    actualizado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    version           INTEGER     NOT NULL DEFAULT 1
);

CREATE TABLE siniestros_w.hito (
    id            BIGSERIAL PRIMARY KEY,
    siniestro_id  BIGINT      NOT NULL REFERENCES siniestros_w.siniestro(id),
    tipo          TEXT        NOT NULL,
    descripcion   TEXT        NOT NULL,
    actor         TEXT        NOT NULL,
    ocurrido_en   TIMESTAMPTZ NOT NULL
);

CREATE TABLE siniestros_w.documento (
    id            BIGSERIAL PRIMARY KEY,
    siniestro_id  BIGINT      NOT NULL REFERENCES siniestros_w.siniestro(id),
    tipo          TEXT        NOT NULL,
    estado        TEXT        NOT NULL,
    cargado_en    TIMESTAMPTZ NOT NULL
);

CREATE TABLE siniestros_w.peritaje (
    id            BIGSERIAL PRIMARY KEY,
    siniestro_id  BIGINT      NOT NULL REFERENCES siniestros_w.siniestro(id),
    perito        TEXT        NOT NULL,
    estado        TEXT        NOT NULL,
    resultado     TEXT,
    agendado_para TIMESTAMPTZ
);

CREATE INDEX idx_hito_siniestro      ON siniestros_w.hito(siniestro_id);
CREATE INDEX idx_documento_siniestro ON siniestros_w.documento(siniestro_id);
CREATE INDEX idx_peritaje_siniestro  ON siniestros_w.peritaje(siniestro_id);
```

> **Los índices están presentes deliberadamente.** La línea base debe ser una implementación razonablemente optimizada, no un hombre de paja. Si el brazo A pierde por falta de índices, el experimento no demuestra nada sobre CQRS.

### `db/init/02_schema_read.sql` — proyección materializada

```sql
CREATE SCHEMA IF NOT EXISTS siniestros_r;

CREATE TABLE siniestros_r.siniestro_estado (
    siniestro_id   BIGINT PRIMARY KEY,
    cliente_id     BIGINT      NOT NULL,
    version        INTEGER     NOT NULL,
    ocurrido_en    TIMESTAMPTZ NOT NULL,   -- timestamp del evento origen
    proyectado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload        JSONB       NOT NULL    -- respuesta completa preconstruida
);

CREATE INDEX idx_estado_cliente ON siniestros_r.siniestro_estado(cliente_id);
```

Un único registro autocontenido por siniestro. La lectura del brazo B es un acceso por clave primaria sin *joins* ni agregaciones.

---

## 6. Contrato de eventos de dominio

**Topic:** `siniestros.eventos` — particionado por `siniestro_id` para garantizar orden por agregado.

```json
{
  "event_id": "a3f1c2e8-...",
  "event_type": "SiniestroEstadoCambiado",
  "siniestro_id": 482913,
  "version": 12,
  "ocurrido_en": "2026-08-24T14:22:03.412Z",
  "payload": {
    "numero": "SIN-2026-482913",
    "cliente_id": 90211,
    "estado": "EN_PERITAJE",
    "causa": "COLISION",
    "monto_estimado": 4200000.00,
    "monto_aprobado": null,
    "fecha_ocurrencia": "2026-08-19T08:10:00Z",
    "fecha_aviso": "2026-08-19T09:32:00Z",
    "poliza": {
      "numero": "POL-778120",
      "producto": "AUTOS_TODO_RIESGO",
      "suma_asegurada": 85000000.00
    },
    "hitos": [
      { "tipo": "AVISO_RECIBIDO", "descripcion": "Aviso registrado por canal móvil",
        "actor": "CLIENTE", "ocurrido_en": "2026-08-19T09:32:00Z" }
    ],
    "documentos": [
      { "tipo": "FOTOS_VEHICULO", "estado": "APROBADO",
        "cargado_en": "2026-08-19T10:05:00Z" }
    ],
    "peritaje": {
      "perito": "P-3391", "estado": "AGENDADO",
      "resultado": null, "agendado_para": "2026-08-25T15:00:00Z"
    }
  }
}
```

**Decisiones de contrato:**

- **Event-carried state transfer** — el evento transporta el estado completo. El proyector no consulta de vuelta el modelo de escritura, lo que preserva el desacople exigido por HA-08.
- **Idempotencia por `version`** — el *upsert* sólo aplica si la versión entrante es mayor que la almacenada. Reprocesar un evento no corrompe la proyección.
- **`ocurrido_en`** habilita la medición del *lag*, que es una métrica dependiente del experimento.

---

## 7. Implementación de la API y los brazos

### `api/app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    read_strategy: str = "A"
    database_url: str
    redis_url: str = "redis://redis:6379/0"
    db_pool_min: int = 10
    db_pool_max: int = 10
    cache_ttl_seconds: int = 30

settings = Settings()
```

### `api/app/db.py`

```python
import asyncpg
from .config import settings

pool: asyncpg.Pool | None = None

async def init_pool() -> None:
    global pool
    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
        max_inactive_connection_lifetime=0,
        command_timeout=5,
    )

async def close_pool() -> None:
    if pool:
        await pool.close()
```

> **Regla no negociable: driver asíncrono en toda la ruta de lectura.** Un `psycopg2.connect()` dentro de un `async def` bloquea el *event loop* completo y dispara el p95 de forma no lineal bajo carga. Eso produciría una **refutación falsa** de la hipótesis: se estaría midiendo un defecto de implementación, no la insuficiencia de la arquitectura. Si se prefiere código síncrono, los endpoints deben declararse como `def` (sin `async`) para que FastAPI los despache al *threadpool*, manteniendo esa decisión idéntica en los cuatro brazos.

### `api/app/strategies/arm_a.py` — línea base

```python
import orjson
from ..db import pool

SQL = """
SELECT
    s.numero, s.cliente_id, s.estado, s.causa,
    s.monto_estimado, s.monto_aprobado,
    s.fecha_ocurrencia, s.fecha_aviso,
    jsonb_build_object(
        'numero', p.numero,
        'producto', p.producto,
        'suma_asegurada', p.suma_asegurada
    ) AS poliza,
    COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
            'tipo', h.tipo, 'descripcion', h.descripcion,
            'actor', h.actor, 'ocurrido_en', h.ocurrido_en
        ) ORDER BY h.ocurrido_en)
        FROM siniestros_w.hito h WHERE h.siniestro_id = s.id
    ), '[]'::jsonb) AS hitos,
    COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
            'tipo', d.tipo, 'estado', d.estado, 'cargado_en', d.cargado_en
        ) ORDER BY d.cargado_en)
        FROM siniestros_w.documento d WHERE d.siniestro_id = s.id
    ), '[]'::jsonb) AS documentos,
    (
        SELECT jsonb_build_object(
            'perito', pe.perito, 'estado', pe.estado,
            'resultado', pe.resultado, 'agendado_para', pe.agendado_para
        )
        FROM siniestros_w.peritaje pe
        WHERE pe.siniestro_id = s.id
        ORDER BY pe.id DESC LIMIT 1
    ) AS peritaje
FROM siniestros_w.siniestro s
JOIN siniestros_w.poliza p ON p.id = s.poliza_id
WHERE s.id = $1
"""

async def get_estado(siniestro_id: int) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(SQL, siniestro_id)
    if row is None:
        return None
    data = dict(row)
    for k in ("poliza", "hitos", "documentos", "peritaje"):
        if isinstance(data[k], str):
            data[k] = orjson.loads(data[k])
    return data
```

### `api/app/strategies/arm_b.py` — proyección materializada

```python
import orjson
from ..db import pool

SQL = "SELECT payload FROM siniestros_r.siniestro_estado WHERE siniestro_id = $1"

async def get_estado(siniestro_id: int) -> dict | None:
    async with pool.acquire() as conn:
        raw = await conn.fetchval(SQL, siniestro_id)
    return orjson.loads(raw) if raw else None
```

### `api/app/strategies/arm_c.py` — cache-aside

```python
import orjson
from ..cache import redis_client
from ..config import settings
from ..metrics import CACHE_HITS, CACHE_MISSES
from . import arm_b

def key(siniestro_id: int) -> str:
    return f"siniestro:estado:{siniestro_id}"

async def get_estado(siniestro_id: int) -> dict | None:
    cached = await redis_client.get(key(siniestro_id))
    if cached is not None:
        CACHE_HITS.inc()
        return orjson.loads(cached)

    CACHE_MISSES.inc()
    data = await arm_b.get_estado(siniestro_id)
    if data is not None:
        await redis_client.set(
            key(siniestro_id), orjson.dumps(data),
            ex=settings.cache_ttl_seconds,
        )
    return data


async def get_estado_raw(siniestro_id: int) -> bytes | None:
    """Brazo C': devuelve bytes JSON sin re-serializar (bypass de Pydantic)."""
    cached = await redis_client.get(key(siniestro_id))
    if cached is not None:
        CACHE_HITS.inc()
        return cached
    CACHE_MISSES.inc()
    data = await arm_b.get_estado(siniestro_id)
    if data is None:
        return None
    raw = orjson.dumps(data)
    await redis_client.set(key(siniestro_id), raw, ex=settings.cache_ttl_seconds)
    return raw
```

### `api/app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import ORJSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import settings
from .db import init_pool, close_pool
from .cache import init_cache, close_cache
from .metrics import REQUEST_LATENCY
from .models import EstadoSiniestro
from .strategies import arm_a, arm_b, arm_c

STRATEGIES = {"A": arm_a.get_estado, "B": arm_b.get_estado, "C": arm_c.get_estado}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await init_cache()
    yield
    await close_pool()
    await close_cache()

app = FastAPI(lifespan=lifespan, default_response_class=ORJSONResponse)

@app.get("/health")
async def health():
    return {"status": "ok", "arm": settings.read_strategy}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/siniestros/{siniestro_id}/estado", response_model=EstadoSiniestro)
async def estado_siniestro(siniestro_id: int):
    arm = settings.read_strategy
    with REQUEST_LATENCY.labels(arm=arm).time():
        if arm == "C_PRIME":
            raw = await arm_c.get_estado_raw(siniestro_id)
            if raw is None:
                raise HTTPException(404, "Siniestro no encontrado")
            return Response(content=raw, media_type="application/json")

        data = await STRATEGIES[arm](siniestro_id)
        if data is None:
            raise HTTPException(404, "Siniestro no encontrado")
        return data
```

### `api/app/metrics.py`

```python
from prometheus_client import Counter, Histogram

REQUEST_LATENCY = Histogram(
    "ha08_read_latency_seconds",
    "Latencia interna de la consulta de estado de siniestro",
    labelnames=("arm",),
    buckets=(0.005, 0.010, 0.025, 0.050, 0.075, 0.100,
             0.150, 0.250, 0.500, 1.0, 2.5),
)
CACHE_HITS = Counter("ha08_cache_hits_total", "Aciertos de caché")
CACHE_MISSES = Counter("ha08_cache_misses_total", "Fallos de caché")
```

> Los *buckets* incluyen **0.150 explícitamente**, que es el umbral del ASR. Sin ese bucket, el p95 calculado por Prometheus se interpola entre 0.100 y 0.250 y pierde precisión justo donde importa.

---

## 8. Proyector y simulador

### `projector/projector.py`

```python
import asyncio, os, orjson
import asyncpg
from aiokafka import AIOKafkaConsumer
from redis.asyncio import Redis
from prometheus_client import Histogram, Counter, start_http_server

LAG = Histogram(
    "ha08_projection_lag_seconds",
    "Lag entre ocurrencia del evento y proyección",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
)
PROJECTED = Counter("ha08_events_projected_total", "Eventos proyectados")
SKIPPED = Counter("ha08_events_skipped_total", "Eventos descartados por versión")

UPSERT = """
INSERT INTO siniestros_r.siniestro_estado
       (siniestro_id, cliente_id, version, ocurrido_en, proyectado_en, payload)
VALUES ($1, $2, $3, $4, now(), $5)
ON CONFLICT (siniestro_id) DO UPDATE
SET cliente_id    = EXCLUDED.cliente_id,
    version       = EXCLUDED.version,
    ocurrido_en   = EXCLUDED.ocurrido_en,
    proyectado_en = now(),
    payload       = EXCLUDED.payload
WHERE siniestros_r.siniestro_estado.version < EXCLUDED.version
RETURNING siniestro_id
"""

async def main() -> None:
    start_http_server(8001)
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=2, max_size=5)
    redis = Redis.from_url(os.environ["REDIS_URL"])
    consumer = AIOKafkaConsumer(
        os.environ["TOPIC"],
        bootstrap_servers=os.environ["KAFKA_BOOTSTRAP"],
        group_id=os.environ["CONSUMER_GROUP"],
        enable_auto_commit=True,
        auto_offset_reset="latest",
    )
    await consumer.start()
    try:
        async for msg in consumer:
            ev = orjson.loads(msg.value)
            async with pool.acquire() as conn:
                applied = await conn.fetchval(
                    UPSERT,
                    ev["siniestro_id"], ev["payload"]["cliente_id"],
                    ev["version"], ev["ocurrido_en"],
                    orjson.dumps(ev["payload"]).decode(),
                )
            if applied is None:
                SKIPPED.inc()
                continue
            # Invalidación proactiva: el caché no debe servir estado vencido
            await redis.delete(f"siniestro:estado:{ev['siniestro_id']}")
            PROJECTED.inc()
            LAG.observe(_lag_seconds(ev["ocurrido_en"]))
    finally:
        await consumer.stop()
        await pool.close()
        await redis.aclose()

if __name__ == "__main__":
    asyncio.run(main())
```

> **Invalidación (`DEL`) frente a precarga (`SET`).** Con `DEL`, la siguiente lectura sufre un fallo y paga el costo de la proyección. Con `SET`, el proyector precarga el caché y elimina el fallo en frío, a costa de escribir en Redis por cada evento aunque nadie consulte ese siniestro. Se empieza con `DEL` por ser la variante conservadora; la precarga es la primera iteración a probar si el brazo C se refuta.

### `simulator/simulator.py`

Bucle principal, a `EVENTS_PER_SECOND`:

```python
# 1. elegir un siniestro del hot set (los que un cliente consultaría)
# 2. UPDATE siniestros_w.siniestro SET estado=..., version = version + 1
# 3. INSERT en siniestros_w.hito
# 4. construir el payload completo (mismo shape que arm_a)
# 5. publicar en Redpanda con key=str(siniestro_id) y ocurrido_en=now()
```

Debe escribir sobre el **conjunto caliente**, no sobre siniestros aleatorios del millón: si actualiza registros que nadie consulta, el caché nunca se invalida y el brazo C obtiene un *hit-rate* irrealmente alto.

---

## 9. Generación del dataset

### `db/init/03_seed.sql`

```sql
-- Pólizas
INSERT INTO siniestros_w.poliza
  (id, cliente_id, numero, producto, estado, suma_asegurada, vigencia_desde, vigencia_hasta)
SELECT g, g, 'POL-' || g,
       (ARRAY['AUTOS_TODO_RIESGO','HOGAR','VIDA','SALUD'])[1 + (g % 4)],
       'VIGENTE', 50000000 + (g % 100) * 1000000,
       DATE '2025-01-01', DATE '2026-12-31'
FROM generate_series(1, 1000000) g;

-- Siniestros
INSERT INTO siniestros_w.siniestro
  (id, poliza_id, cliente_id, numero, estado, causa, monto_estimado,
   fecha_ocurrencia, fecha_aviso, version)
SELECT g, g, g, 'SIN-2026-' || g,
       (ARRAY['RECIBIDO','EN_VALIDACION','EN_PERITAJE','EN_LIQUIDACION','APROBADO','RECHAZADO'])[1 + (g % 6)],
       (ARRAY['COLISION','HURTO','INCENDIO','DANO_AGUA'])[1 + (g % 4)],
       1000000 + (g % 500) * 10000,
       now() - (g % 365) * INTERVAL '1 day',
       now() - (g % 365) * INTERVAL '1 day' + INTERVAL '2 hours',
       1
FROM generate_series(1, 1000000) g;

-- Hitos: 5 por siniestro
INSERT INTO siniestros_w.hito (siniestro_id, tipo, descripcion, actor, ocurrido_en)
SELECT s, (ARRAY['AVISO_RECIBIDO','DOCS_SOLICITADOS','PERITO_ASIGNADO','INSPECCION','LIQUIDACION'])[h],
       'Hito automático ' || h, 'SISTEMA', now() - (h * INTERVAL '1 day')
FROM generate_series(1, 1000000) s, generate_series(1, 5) h;

-- Documentos: 3 por siniestro
INSERT INTO siniestros_w.documento (siniestro_id, tipo, estado, cargado_en)
SELECT s, (ARRAY['FOTOS','FACTURA','DENUNCIA'])[d],
       (ARRAY['PENDIENTE','APROBADO','RECHAZADO'])[1 + ((s + d) % 3)],
       now() - (d * INTERVAL '1 day')
FROM generate_series(1, 1000000) s, generate_series(1, 3) d;

-- Peritaje: 1 por siniestro
INSERT INTO siniestros_w.peritaje (siniestro_id, perito, estado, resultado, agendado_para)
SELECT s, 'P-' || (s % 500),
       (ARRAY['AGENDADO','EN_CURSO','CERRADO'])[1 + (s % 3)],
       NULL, now() + INTERVAL '1 day'
FROM generate_series(1, 1000000) s;

ANALYZE;
```

Luego se precarga la proyección con `04_backfill_projection.sql`, que ejecuta la misma consulta del brazo A para todos los siniestros e inserta el resultado en `siniestros_r.siniestro_estado`. Así los brazos B y C parten de un estado completo y no miden fallos masivos que no ocurrirían en producción.

### Por qué el volumen importa

Con 5 000 siniestros todo cabe en `shared_buffers` y el brazo A saldría artificialmente rápido: se estaría midiendo el caché de páginas de PostgreSQL, no la arquitectura. Con 1 000 000 de siniestros (~2 GB entre tablas e índices) y `shared_buffers=256MB`, el conjunto de trabajo excede la memoria del motor y la línea base enfrenta E/S real, como en producción.

**Verificación obligatoria antes de medir:**

```sql
SELECT pg_size_pretty(pg_total_relation_size('siniestros_w.siniestro')) AS siniestro,
       pg_size_pretty(pg_total_relation_size('siniestros_w.hito'))      AS hito,
       pg_size_pretty(pg_database_size(current_database()))             AS total;
```

El total debe superar cómodamente `shared_buffers + effective_cache_size`. Registrar estos valores en el informe.

> **Tiempo estimado:** la generación produce cerca de 10 millones de filas y puede tardar entre 10 y 20 minutos. Se ejecuta **una sola vez** y se persiste en el volumen `pgdata`; no debe reconstruirse entre brazos.

---

## 10. Perfil de carga

### Distribución de claves

Un cliente consulta **su** siniestro, y los siniestros abiertos recientes concentran las consultas. Una distribución uniforme sobre un millón de claves llevaría el *hit-rate* del caché prácticamente a cero y castigaría injustamente al brazo C.

| Conjunto | Tamaño | Proporción de consultas |
|---|---|---|
| **Caliente** (siniestros abiertos recientes) | 10 000 | 80 % |
| **Frío** (histórico completo) | 1 000 000 | 20 % |

Se usa este modelo explícito de dos conjuntos en lugar de un ajuste zipfiano porque es más fácil de justificar y de reproducir en el informe.

### `load/k6/read_estado.js`

```javascript
import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://api:8000';
const ARM = __ENV.ARM || 'A';
const HOT_SET_SIZE = 10000;
const TOTAL = 1000000;
const HOT_RATIO = 0.8;

const latencia = new Trend('ha08_estado_duration', true);

export const options = {
  discardResponseBodies: false,
  scenarios: {
    escalones: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 400,
      stages: [
        { target: 10, duration: '1m' },   // warm-up — SE DESCARTA
        { target: 10, duration: '3m' },
        { target: 25, duration: '3m' },
        { target: 50, duration: '3m' },
        { target: 80, duration: '3m' },
      ],
    },
  },
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    'ha08_estado_duration': ['p(95)<150'],
  },
  tags: { arm: ARM, run_id: __ENV.RUN_ID || 'r1' },
};

function pickId() {
  if (Math.random() < HOT_RATIO) {
    return 1 + Math.floor(Math.random() * HOT_SET_SIZE);
  }
  return 1 + Math.floor(Math.random() * TOTAL);
}

export default function () {
  const id = pickId();
  const res = http.get(`${BASE_URL}/siniestros/${id}/estado`, {
    tags: { name: 'GET /siniestros/{id}/estado' },
  });
  latencia.add(res.timings.duration);
  check(res, {
    'status 200': (r) => r.status === 200,
    'tiene estado': (r) => r.json('estado') !== undefined,
  });
}
```

**Notas sobre el perfil:**

- `ramping-arrival-rate` fija la **tasa de llegada**, no el número de usuarios virtuales. Es lo correcto para medir latencia: con `ramping-vus`, si el servicio se degrada la carga baja sola y el p95 queda enmascarado.
- El primer minuto es calentamiento y **se descarta del análisis**: cubre el llenado de *pools*, la compilación de bytecode y el calentamiento de los planes de PostgreSQL.
- El `threshold` de 150 ms hace que k6 marque la corrida como fallida automáticamente si no se cumple: es el criterio de aceptación codificado.

---

## 11. Protocolo de ejecución

### `scripts/run_experiment.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ARM="${1:?Uso: run_experiment.sh <A|B|C|C_PRIME> <run_id>}"
RUN_ID="${2:?Falta run_id}"

echo "==> Corrida ${RUN_ID}, brazo ${ARM}"

# 1. Reiniciar estado volátil: caché vacío, pools frescos, shared_buffers limpio
docker compose stop api projector simulator
docker compose exec -T redis redis-cli FLUSHALL
docker compose restart postgres
docker compose exec -T postgres sh -c 'until pg_isready -U solventa; do sleep 1; done'

# 2. Arrancar con la estrategia del brazo
READ_STRATEGY="${ARM}" docker compose up -d api projector simulator
sleep 20   # estabilización de pools y consumer group

# 3. Verificar paridad del payload entre brazos
./scripts/verify_parity.sh

# 4. Ejecutar la carga
READ_STRATEGY="${ARM}" RUN_ID="${RUN_ID}" \
  docker compose --profile load run --rm k6

# 5. Recolectar métricas de recursos y del proyector
docker stats --no-stream --format \
  "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" > "results/raw/stats_${ARM}_${RUN_ID}.csv"
curl -s localhost:8001/metrics | grep ha08_projection_lag \
  > "results/raw/lag_${ARM}_${RUN_ID}.txt"

echo "==> Listo: results/raw/summary_${ARM}_${RUN_ID}.json"
```

### `scripts/verify_parity.sh`

```bash
#!/usr/bin/env bash
# Verifica que los brazos devuelvan el mismo JSON para el mismo siniestro.
# Si difieren, parte de la latencia medida vendría del tamaño del payload
# y la comparación entre brazos quedaría invalidada.
set -euo pipefail
ID=42
for ARM in A B C; do
  READ_STRATEGY=$ARM docker compose up -d api >/dev/null
  sleep 8
  curl -s "http://localhost:8000/siniestros/${ID}/estado" | jq -S . > "/tmp/parity_${ARM}.json"
done
diff /tmp/parity_A.json /tmp/parity_B.json && diff /tmp/parity_B.json /tmp/parity_C.json \
  && echo "OK: payload idéntico entre brazos" \
  || { echo "ERROR: los brazos devuelven payloads distintos"; exit 1; }
```

### Secuencia completa

El orden de brazos está contrabalanceado según el cuadrado latino definido en el documento de diseño (Anexo A):

```bash
# Preparación (una sola vez)
docker compose up -d postgres redis redpanda prometheus grafana
docker compose exec postgres psql -U solventa -d solventa \
  -f /docker-entrypoint-initdb.d/03_seed.sql
docker compose exec postgres psql -U solventa -d solventa \
  -f /docker-entrypoint-initdb.d/04_backfill_projection.sql

# Corridas contrabalanceadas
./scripts/run_experiment.sh A r1 && ./scripts/run_experiment.sh B r1 && ./scripts/run_experiment.sh C r1
./scripts/run_experiment.sh B r2 && ./scripts/run_experiment.sh C r2 && ./scripts/run_experiment.sh A r2
./scripts/run_experiment.sh C r3 && ./scripts/run_experiment.sh A r3 && ./scripts/run_experiment.sh B r3

# Punto de sensibilidad 2: TTL del caché
CACHE_TTL_SECONDS=0   ./scripts/run_experiment.sh C ttl0
CACHE_TTL_SECONDS=300 ./scripts/run_experiment.sh C ttl300

# Factor adicional: serialización
./scripts/run_experiment.sh C_PRIME r1

# Consolidación
./scripts/collect_results.sh > results/consolidado.csv
```

---

## 12. Métricas recolectadas

| Métrica | Fuente | Uso |
|---|---|---|
| `ha08_estado_duration` p50/p95/p99 | k6 | **Métrica principal** (extremo a extremo) |
| `ha08_read_latency_seconds` p95 | API / Prometheus | Latencia interna; su diferencia con k6 revela el costo del stack ASGI/HTTP |
| `http_req_failed` | k6 | Tasa de error |
| `ha08_projection_lag_seconds` p95 | Proyector | *Staleness* de la proyección |
| `ha08_cache_hits_total` / `_misses_total` | API | *Hit-rate* del brazo C |
| `ha08_events_projected_total` | Proyector | Confirma que el simulador estuvo activo |
| CPU / memoria por contenedor | `docker stats` | Detección de saturación |
| `dropped_iterations` | k6 | Validez de la corrida |

La medición simultánea de la latencia en el cliente y en el servidor permite separar el costo del transporte del costo de la estrategia de lectura, que es el dato que hace defendible el informe.

---

## 13. Verificaciones de sanidad

Antes de dar por válida una corrida:

- [ ] `dropped_iterations` en el resumen de k6 es 0 o despreciable — si no, **k6 es el cuello de botella** y la corrida no sirve.
- [ ] Ningún contenedor de infraestructura (postgres, redis, redpanda) al 100 % de su límite de CPU.
- [ ] `ha08_events_projected_total` creció de forma sostenida durante toda la ventana: el simulador estuvo activo y la proyección bajo actualización real.
- [ ] Tasa de error < 1 %.
- [ ] La verificación de paridad de payload pasó.
- [ ] El tamaño de la base supera `shared_buffers + effective_cache_size`.

---

## 14. Solución de problemas

| Síntoma | Causa probable | Acción |
|---|---|---|
| p95 del brazo A sospechosamente bajo (< 20 ms) | El dataset cabe en memoria | Verificar el tamaño de la base y reducir `shared_buffers` |
| p95 se dispara de forma no lineal al subir la carga | Driver síncrono bloqueando el *event loop*, o *pool* agotado | Revisar que toda la ruta use `asyncpg`; comparar `DB_POOL_MAX` con la concurrencia |
| *Hit-rate* del brazo C cercano al 100 % | El simulador no está escribiendo sobre el conjunto caliente | Revisar `HOT_SET_SIZE` en el simulador |
| *Hit-rate* del brazo C cercano a 0 % | Distribución de claves uniforme, o TTL demasiado corto | Revisar `HOT_RATIO` en el script de k6 y `CACHE_TTL_SECONDS` |
| `dropped_iterations` alto | k6 saturado | Aumentar `preAllocatedVUs` o el límite de CPU del contenedor de k6 |
| Lag de proyección creciente | El proyector no alcanza el ritmo de eventos | Revisar su límite de CPU y el tamaño de su *pool* |
| El proyector no consume nada | `auto_offset_reset=latest` con eventos previos al arranque | Arrancar el proyector antes que el simulador |

---

## 15. Anexo — Comandos de referencia

```bash
# Levantar infraestructura
docker compose up -d postgres redis redpanda prometheus grafana

# Ver logs del proyector
docker compose logs -f projector

# Consultar lag actual
curl -s localhost:8001/metrics | grep ha08_projection_lag

# Hit-rate del caché
curl -s localhost:8000/metrics | grep ha08_cache

# Plan de ejecución del brazo A (verificar uso de índices)
docker compose exec postgres psql -U solventa -d solventa \
  -c "EXPLAIN (ANALYZE, BUFFERS) SELECT ... WHERE s.id = 42;"

# Tamaño de la base
docker compose exec postgres psql -U solventa -d solventa \
  -c "SELECT pg_size_pretty(pg_database_size(current_database()));"

# Uso de recursos en vivo durante una corrida
docker stats

# Limpiar todo (elimina el dataset: obliga a regenerarlo)
docker compose down -v
```
