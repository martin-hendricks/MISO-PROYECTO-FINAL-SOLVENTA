# ms-siniestros

Aviso, evaluación, aprobación y pago de siniestros; automatización de siniestros paramétricos.

**Stack:** Python (FastAPI)
**ASRs relevantes:** EC-LAT-11 (consulta de estado, p95 ≤ 150ms — ver `experiments/ha-08-lectura-siniestro`), EC-DISP-02

CQRS: separación comando/consulta pendiente de aplicar según el resultado del experimento HA-08.

## Historias cubiertas

| HU | Jira | Qué resuelve |
| --- | --- | --- |
| HU-30 · Estados del siniestro | [SOLV-123](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-123) | Modelo único de estados (`recibido`, `en_evaluacion`, `decidido`, `enrutado`, `pagado`) con transiciones explícitas, traza con marca de tiempo y origen, y rechazo atómico de transiciones inválidas. |
| HU-32 · Recibir evento paramétrico (stub) | [SOLV-125](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-125) | `POST /v1/eventos-parametricos` ingiere un evento simulado (id + valor comparable) de forma idempotente por `evento_id`, persistido antes de evaluarse. |
| HU-33 · Evaluar umbral paramétrico | [SOLV-126](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-126) | Compara el valor del evento contra un umbral que viaja en la misma solicitud; evaluación determinista, con el resultado (umbral, valor, decisión, motivo) siempre persistido. |
| HU-34 · Disparar pago paramétrico (stub) | [SOLV-127](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-127) | Si el umbral se cumple, dispara un desembolso simulado sin intervención humana, idempotente por `evento_id`, y mueve el siniestro a `pagado`. |

### Estados del siniestro (HU-30)

`app/domain/modelos.py` (`Siniestro`, `EstadoSiniestro`, `TransicionEstado`) es el **modelo único** de estado del siniestro: todos los canales futuros (cola del operador, decisión, pago, lista del cliente) leerían de este mismo agregado. Las transiciones válidas están declaradas explícitamente:

```
recibido -> en_evaluacion -> decidido -> enrutado -> pagado
```

No existe transición directa a `pagado` sin pasar por `decidido`, ni manera de retroceder a `recibido`. `Siniestro.cambiar_estado` valida antes de mutar: una transición inválida lanza `TransicionInvalida` sin dejar el agregado en un estado intermedio ni confirmar la transacción (`app/application/casos_uso.py::cambiar_estado_siniestro`). Cada transición queda en `siniestro_transicion` con `ocurrido_en` y `origen` (de quién/qué vino el cambio), reconstruyendo la traza completa.

### Evento paramétrico (HU-32)

`POST /v1/eventos-parametricos` ingiere `{evento_id, valor}`, propio de Solventa (no el esquema del proveedor real de vuelos/clima). `evento_id` es la clave de idempotencia (`UNIQUE` en `evento_parametrico.evento_id`): reingestar el mismo id no dispara una segunda evaluación ni un segundo pago — se detecta por colisión de la restricción `UNIQUE` en el commit (`ClaveIdempotenciaDuplicada`, mismo patrón que `ms-arquetipo`/`ms-cotizacion`) y también de forma determinista al leer el evento antes de intentar insertarlo. El evento se persiste con `recibido_en` **antes** de evaluarse (auditable). Un evento sin id o con valor no numérico se rechaza con `EventoParametricoInvalido` (422) y nunca entra a la cadena de evaluación. El puerto `RepositorioEventosParametricos` (en `app/ports/persistencia.py`) es el único punto por el que entra el evento: cambiar el stub de ingesta HTTP por un feed real no altera `application/` ni `domain/`.

### Evaluación de umbral (HU-33) — decisión de diseño: sin red a ms-polizas

**`ms-siniestros` NO llama por red a `ms-polizas` en este alcance.** El umbral y la vigencia de la póliza viajan como parámetros en la misma solicitud de ingesta (`umbral`, `poliza_vigente` en el cuerpo de `POST /v1/eventos-parametricos`), no se resuelven contra otro microservicio. Esta es una simplificación deliberada: como `ms-polizas` es otro microservicio y este alcance no incluye integración cross-service, se modela el umbral/vigencia como un dato simple asociado a la solicitud de evaluación. Un adaptador futuro que resuelva el umbral real contra `ms-polizas` reemplazaría solo la fuente de ese parámetro antes de invocar `evaluar_umbral`, sin tocar el dominio.

La evaluación es determinista: `EvaluacionUmbral.evaluar(evento, umbral, poliza_vigente)` siempre devuelve la misma decisión para la misma entrada. Si `poliza_vigente` es falso, la decisión es `False` con motivo `poliza_no_vigente`, sin importar el valor. Si la póliza está vigente, se paga cuando `valor >= umbral` (`umbral_cumplido`); si no, queda `umbral_no_alcanzado`. El resultado completo (umbral, valor, vigencia, decisión, motivo) se persiste siempre en `evaluacion_umbral`, se pague o no.

### Pago paramétrico (HU-34)

Si la evaluación decide pagar, `disparar_pago_parametrico` dispara el desembolso **sin intervención humana** a través del puerto `AdaptadorDesembolso` (`app/ports/pagos.py`). La implementación provista, `AdaptadorDesembolsoStub` (`app/infrastructure/pagos.py`), es un stub sustituible: solo registra el desembolso en memoria, sin red de pagos real. Sustituir el stub por una pasarela real (p. ej. `ms-pagos`) no requiere cambiar `application/` ni `domain/`, solo cumplir el `Protocol`. El pago es idempotente por `evento_id` (`UNIQUE` en `pago_parametrico.evento_id`): reprocesar el mismo evento no genera un segundo desembolso, se conserva el original. Al pagar, el siniestro transiciona a `pagado` usando la máquina de estados de HU-30, con monto y marca de tiempo persistidos en `pago_parametrico`.

## Estructura (hexagonal)

```
app/
├── main.py              crear_app(): lifespan, manejo de errores de dominio → HTTP
├── config.py            pydantic-settings (variables de entorno / .env)
├── dependencies.py      raíz de composición: qué implementación cumple cada puerto
├── observabilidad.py    /health, /metrics (Prometheus), X-Correlation-Id
├── api/v1/              POST /v1/eventos-parametricos, GET/POST /v1/siniestros...
├── domain/              Siniestro, EventoParametrico, EvaluacionUmbral, PagoParametrico
├── application/         casos de uso: recibir_evento_parametrico, evaluar_umbral, disparar_pago_parametrico, cambiar_estado_siniestro
├── ports/                persistencia.py (repos + UoW) y pagos.py (AdaptadorDesembolso)
└── infrastructure/      sql.py (SQLAlchemy 2 async + outbox) y pagos.py (stub de desembolso)
db/01_ms_siniestros.sql              copia literal del DDL oficial (reclamación manual)
db/02_ms_siniestros_parametrico.sql  copia literal de la extensión aditiva de estas HU
tests/                  PyTest sin red ni BD (dobles de los puertos) + integración marcada
```

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
docker build --target test -t ms-siniestros:test . && docker run --rm ms-siniestros:test
```

## Ejecutar con Docker (HU-71)

```bash
docker compose up --build          # servicio en :8080 + PostgreSQL 16 con el DDL de db/
```

La imagen fija el runtime (`python:3.12.7-slim-bookworm`, nunca `latest`) y corre con un usuario sin privilegios (uid 1000). El puerto 8080 y el uid son los que espera el chart `infra/k8s/charts/microservicio`; con `uvicorn` local sin Docker el servicio sigue en :8000.

## Despliegue

Imagen `runtime` del `Dockerfile` hacia EKS (vista de despliegue §1.1.3). El DDL oficial del servicio está en `db/schema/08_ms_siniestros.sql` (reclamación manual) y `db/schema/13_ms_siniestros_parametrico.sql` (extensión aditiva de HU-30/32/33/34) del repo; el schema `ms_siniestros` vive en la instancia compartida que provisiona Terraform. Sobre ella se aplican, en orden, los archivos de `db/` de este servicio.
