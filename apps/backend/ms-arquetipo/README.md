# ms-arquetipo

Plantilla de **microservicio del núcleo** de Solventa (`ms-cotizacion`, `ms-polizas`, `ms-siniestros`...). No se despliega: se copia con `scripts/nuevo-servicio.sh ms <nombre>`.

Un microservicio **resuelve el negocio**. Tiene reglas de dominio, su propio almacén (un schema por servicio) y publica eventos. No lo llama el canal: lo llaman los BFF y `api-socios` por la red interna, y no valida JWT porque eso ya lo hizo el borde.

## Estructura (hexagonal)

```
app/
├── main.py              crear_app(): lifespan, manejo de errores de dominio → HTTP
├── config.py            pydantic-settings (variables de entorno / .env)
├── dependencies.py      raíz de composición: qué implementación cumple cada puerto
├── observabilidad.py    /health, /metrics (Prometheus), X-Correlation-Id
├── api/v1/              interfaz provista (ICotizacion, IPolizas...): rutas + DTO
├── domain/              entidades y reglas puras: sin FastAPI, sin SQL (GRASP Experto)
├── application/         casos de uso: orquestan dominio + puertos (SRP / OCP)
├── ports/               interfaces que la aplicación necesita (DIP)
└── infrastructure/      adaptadores: SQLAlchemy 2 async + transactional outbox
db/01_ms_arquetipo.sql   DDL del almacén (desarrollo local)
tests/                   PyTest sin red ni BD (dobles de los puertos) + integración marcada
```

La dependencia va **hacia adentro**: `api → application → domain`, e `infrastructure` implementa `ports`. El dominio no importa nada de FastAPI ni de SQLAlchemy.

## Qué trae resuelto el ejemplo (`Ejemplo`)

| Patrón | Dónde | Para qué |
| --- | --- | --- |
| Comando **idempotente** (`Idempotency-Key`) | `casos_uso.registrar_ejemplo` | Un reintento devuelve el mismo registro (201 la primera vez, 200 en el reintento). Incluye la carrera entre dos peticiones concurrentes |
| **Transactional outbox** | `infrastructure/sql.py` (`OutboxSQL`) | El cambio y su evento se confirman en la misma transacción. Un relay publica en Kafka (`db/README.md`) |
| Regla de negocio en la entidad | `Ejemplo.registrar`, `Ejemplo.aprobar` | Errores de dominio → 404 / 409 / 422 con `{codigo, mensaje}` |
| Puertos + doble en memoria | `ports/`, `tests/dobles.py` | Tests del núcleo sin PostgreSQL ni red (HU-85) |

<!-- desarrollo -->

## Desarrollo

**Requisitos:** Python 3.12+.

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
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/solventa pytest -m integration
```

En CI las unitarias corren con el workflow de backend del PR #10 (`backend-unit-tests.yml`), con cobertura y reporte JUnit. Las pruebas marcadas `integration` por ahora se corren en local.
