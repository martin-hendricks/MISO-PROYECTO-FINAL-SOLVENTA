# analitica

Microservicio del núcleo de Solventa que agrega métricas de ciclo de vida de póliza (HU-68)
a partir de `BusEventos` (MSK) y las expone de solo lectura para el dashboard de back-office
(HU-69). No persiste nada por evento individual: solo un contador por (tipo, fecha).

## Estructura (hexagonal)

```
app/
├── main.py                  crear_app(): lifespan, wiring de motor/UoW/consumidor, errores → HTTP
├── config.py                pydantic-settings (variables de entorno / .env)
├── dependencies.py          raíz de composición: UoW
├── seguridad.py             JWT HS256 (mismo SOLVENTA_TOKEN_SECRET), LlamanteDep
├── observabilidad.py        /health, /metrics (Prometheus), X-Correlation-Id
├── api/v1/                  rutas + DTO de /v1/metricas
├── domain/                  ConteoEventos, EventoBus (contrato del bus)
├── application/              manejar_evento() (consumidor), listar_metricas() (API)
├── ports/                   persistencia.py (interfaz, DIP)
└── infrastructure/          SQLAlchemy 2 async + ConsumidorMSK (IAM/aiokafka)
db/01_analitica.sql          DDL idempotente del schema analitica
tests/                       PyTest sin red ni BD (dobles) + integración marcada
```

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/v1/metricas?desde=YYYY-MM-DD&hasta=YYYY-MM-DD` | Conteos agregados por tipo y fecha en el rango. Solo rol `operador` (403 si no) |

No hay endpoint de escritura: los conteos los genera el consumidor de MSK vía
`manejar_evento`, idempotente por `evento_id` (tabla `evento_procesado`).

## Tipos de evento soportados

`PolizaEmitida`, `PolizaRenovada`, `PolizaModificada`, `PolizaCancelada` (de `ms-polizas`,
vía `outbox-relay`), y `PolizaPorVencer` (de `ms-polizas` HU-67, el orquestador de avisos
de vencimiento). Cualquier otro tipo se ignora.

## Variables de entorno

| Variable | Default | Uso |
| --- | --- | --- |
| `SERVICE_NAME` | `analitica` | Título del servicio |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/solventa` | Almacén propio |
| `DB_POOL_SIZE` | `10` | Conexiones por réplica |
| `LOG_LEVEL` | `INFO` | |
| `SOLVENTA_TOKEN_SECRET` | — (obligatoria) | Secreto HS256 compartido con el resto del ecosistema |
| `MSK_BOOTSTRAP_BROKERS` | vacío | Brokers de MSK; sin esto no se arranca ningún consumidor |
| `MSK_TOPIC` | `BusEventos` | Tópico del bus |
| `MSK_CONSUMER_GROUP` | `analitica-cg` | Grupo del consumidor |
| `MSK_AUTH_MECHANISM` | `AWS_MSK_IAM` | Autenticación de MSK |

## Desarrollo

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
export SOLVENTA_TOKEN_SECRET=cambiar-en-local
uvicorn app.main:app --reload                       # http://localhost:8000/docs
```

## Pruebas

```bash
cd apps/backend/analitica
pytest -m "not integration and not contract" --allow-hosts=127.0.0.1,::1
```

Integración contra PostgreSQL 16 con el DDL aplicado:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/solventa pytest -m integration
```

## Despliegue

Imagen `runtime` hacia EKS (`infra/k8s/charts/microservicio`, values en
`infra/k8s/values/analitica.yaml`). Necesita IRSA (rol de consumidor MSK) y el secreto
`SOLVENTA_TOKEN_SECRET` vía `ExternalSecret`, igual patrón que `notificaciones`.
