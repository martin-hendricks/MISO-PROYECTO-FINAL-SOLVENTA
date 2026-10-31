# Backend · Solventa

Python 3.12 + FastAPI. Cada carpeta es un servicio independiente en build y despliegue. Arquitectura: [Hoja de trabajo semana 8 §1.1–1.2](https://github.com/martin-hendricks/MISO-PROYECTO-FINAL-SOLVENTA/wiki/Hoja-de-trabajo-semana-8).

```
 App Android ──► bff-movil ─┐
 Web cliente ─┐             ├──► ms-identidad, ms-cotizacion, ms-polizas, ms-siniestros, ms-pagos …
 Back-office ─┴► bff-web  ──┘            (núcleo: dominio + almacén propio + eventos)
      canal        BORDE                 ──► adaptadores OF/OD/KYC/pasarela, Kafka (solo el núcleo)
```

| Capa | Carpetas | Qué hace |
| --- | --- | --- |
| **Borde** (BFF) | `bff-web`, `bff-movil` | Expone la API del canal; valida JWT y rol; compone llamadas al núcleo. Sin BD |
| **Núcleo** | `ms-*` | Reglas de negocio, su propio schema (`db/schema/`), eventos por outbox |
| **Canal socio** | `api-socios` | API embebida para socios (fuera del alcance de los BFF) |
| **Arquetipos** | `ms-arquetipo`, `bff-arquetipo` | Plantillas probadas; no se despliegan |

## Crear un servicio

```bash
apps/backend/scripts/nuevo-servicio.sh ms  ms-cotizacion
apps/backend/scripts/nuevo-servicio.sh bff bff-web
```

Copia el arquetipo, lo renombra y conserva el `README.md` que ya tenga la carpeta. Si la carpeta ya tiene código, aborta.

## Levantar todo local

```bash
cd apps/backend && ./levantar-local.sh
```

Construye las imágenes, levanta `docker-compose.yml` completo (un Postgres por microservicio + `api-socios` + `bff-web` + `bff-movil`) y aplica las migraciones de cada servicio que falten contra las bases ya corriendo. Es seguro correrlo repetidas veces: no reaplica lo que ya está al día.

Por qué hace falta el script y no basta con `docker compose up -d --build`: `docker-entrypoint-initdb.d` (los `.sql` de cada `<servicio>/db/`) solo corre la primera vez que Postgres crea el volumen de datos. Si ya tenías el stack levantado de antes y alguien agrega una migración nueva en su PR (una columna, una tabla), un `docker compose up` normal no la aplica a tu volumen existente — el servicio levanta pero sus queries fallan con `column ... does not exist`. `./levantar-local.sh` lleva un registro (`schema_migrations`, mismo mecanismo que usa `infra/k8s/platform/run-migrations.sh` en el cluster real) de qué migración ya corrió en cada base local y aplica solo las que falten.

```bash
./levantar-local.sh --no-build   # si ya compilaste las imágenes y solo quieres poner el esquema al día
```

Frontend, en otra terminal: `cd apps/web && pnpm start` (`http://localhost:4200`, con proxy real hacia `bff-web`).

## Pruebas y CI

Cada proyecto: `pip install -e ".[test]" && pytest -m "not integration and not contract" --allow-hosts=127.0.0.1,::1 --cov`.

El CI de backend es el workflow `backend-unit-tests.yml` del PR #10: corre las pruebas unitarias de los servicios que cambiaron, con cobertura y reporte JUnit. Un test rojo falla el pipeline (HU-85).

| Marcador | Corre en |
| --- | --- |
| *(sin marcador)* | Workflow unitario: sin red ni BD |
| `integration` | En local, contra un PostgreSQL con el DDL del servicio (aún no corre en CI) |
| `contract` | Verificación Pact (HU-88), pendiente |

## Estado

| Servicio | Estado |
| --- | --- |
| `bff-web`, `bff-movil` | Solo README; se implementan sobre `bff-arquetipo` en sus HU |
| `ms-*` restantes | Solo README; generar con el script al tomar su HU |
