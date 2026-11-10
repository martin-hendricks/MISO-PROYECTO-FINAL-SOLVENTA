# ms-siniestros

Aviso, evaluación, aprobación y pago de siniestros (asistido y paramétrico), con evidencia en S3 y aprobación asíncrona por motor de reglas.

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
| HU-157 · Aviso de siniestro en el portal y back-office | [SOLV-256](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-256) | Alta del aviso asistido con evidencia en S3 (N5/N6), motor de reglas que aprueba y paga el bajo monto, rechaza lo objetivo o retiene para el operador (N15), cola del operador con decisión auditada (HU-26/27), perito (HU-28) y pago de bajo monto idempotente (HU-29). |
| HU-160 · Lista de siniestros en el portal | [SOLV-259](https://uniandes-team-proyecto.atlassian.net/browse/SOLV-259) | `GET /v1/siniestros?usuario_id=` y `GET /v1/siniestros/{id}/detalle?usuario_id=` (el cliente nunca ve un siniestro ajeno). |
| Billetera · depósitos recibidos | SOLV-144 / SOLV-145 | `GET /v1/pagos-recibidos` y `GET /v1/pagos-recibidos/{id}`: pagos ejecutados del cliente (asistido con intento `ejecutado`, o paramétrico pagado). El evento paramétrico acepta `usuario_id`, `ramo` (máx. 60), `poliza_numero` (máx. 60) y `descripcion` (máx. 200), todos opcionales. `pago_parametrico.comprobante` es `CMP-` + 10 hex y no cambia en una reingesta. |

### Estados del siniestro (HU-30)

`app/domain/modelos.py` (`Siniestro`, `EstadoSiniestro`, `TransicionEstado`) es el **modelo único** de estado del siniestro: todos los canales futuros (cola del operador, decisión, pago, lista del cliente) leerían de este mismo agregado. Las transiciones válidas están declaradas explícitamente:

```
recibido -> en_evaluacion -> decidido -> enrutado -> pagado
```

No existe transición directa a `pagado` sin pasar por `decidido`, ni manera de retroceder a `recibido`. `Siniestro.cambiar_estado` valida antes de mutar: una transición inválida lanza `TransicionInvalida` sin dejar el agregado en un estado intermedio ni confirmar la transacción (`app/application/casos_uso.py::cambiar_estado_siniestro`). Cada transición queda en `siniestro_transicion` con `ocurrido_en` y `origen` (de quién/qué vino el cambio), reconstruyendo la traza completa.

### Billetera (`GET /v1/pagos-recibidos`)

Lectura de los depósitos ya ejecutados de un cliente. Entra un siniestro `pagado` con `pago_siniestro` y al menos un intento `ejecutado`, o un siniestro `pagado` con `pago_parametrico`. El monto es el del pago, nunca la reserva. El total es la suma en `Decimal` y el orden es `pagado_en` descendente. Un paramétrico sin `usuario_id` se paga igual y no aparece en ninguna billetera.

`POST /v1/eventos-parametricos` acepta, opcionales, `usuario_id`, `ramo` (hasta 60), `poliza_numero` (hasta 60) y `descripcion` (hasta 200). El pago paramétrico guarda `comprobante` (`CMP-` y diez hex del id), único y estable ante una reingesta. Migración: `db/07_pago_parametrico_comprobante.sql`.

### Evento paramétrico (HU-32)

`POST /v1/eventos-parametricos` ingiere `{evento_id, valor}`, propio de Solventa (no el esquema del proveedor real de vuelos/clima). `evento_id` es la clave de idempotencia (`UNIQUE` en `evento_parametrico.evento_id`): reingestar el mismo id no dispara una segunda evaluación ni un segundo pago — se detecta por colisión de la restricción `UNIQUE` en el commit (`ClaveIdempotenciaDuplicada`, mismo patrón que `ms-arquetipo`/`ms-cotizacion`) y también de forma determinista al leer el evento antes de intentar insertarlo. El evento se persiste con `recibido_en` **antes** de evaluarse (auditable). Un evento sin id o con valor no numérico se rechaza con `EventoParametricoInvalido` (422) y nunca entra a la cadena de evaluación. El puerto `RepositorioEventosParametricos` (en `app/ports/persistencia.py`) es el único punto por el que entra el evento: cambiar el stub de ingesta HTTP por un feed real no altera `application/` ni `domain/`.

### Evaluación de umbral (HU-33) — decisión de diseño: sin red a ms-polizas

**`ms-siniestros` NO llama por red a `ms-polizas` en este alcance.** El umbral y la vigencia de la póliza viajan como parámetros en la misma solicitud de ingesta (`umbral`, `poliza_vigente` en el cuerpo de `POST /v1/eventos-parametricos`), no se resuelven contra otro microservicio. Esta es una simplificación deliberada: como `ms-polizas` es otro microservicio y este alcance no incluye integración cross-service, se modela el umbral/vigencia como un dato simple asociado a la solicitud de evaluación. Un adaptador futuro que resuelva el umbral real contra `ms-polizas` reemplazaría solo la fuente de ese parámetro antes de invocar `evaluar_umbral`, sin tocar el dominio.

La evaluación es determinista: `EvaluacionUmbral.evaluar(evento, umbral, poliza_vigente)` siempre devuelve la misma decisión para la misma entrada. Si `poliza_vigente` es falso, la decisión es `False` con motivo `poliza_no_vigente`, sin importar el valor. Si la póliza está vigente, se paga cuando `valor >= umbral` (`umbral_cumplido`); si no, queda `umbral_no_alcanzado`. El resultado completo (umbral, valor, vigencia, decisión, motivo) se persiste siempre en `evaluacion_umbral`, se pague o no.

### Pago paramétrico (HU-34)

Si la evaluación decide pagar, `disparar_pago_parametrico` dispara el desembolso **sin intervención humana** a través del puerto `AdaptadorDesembolso` (`app/ports/pagos.py`). La implementación provista, `AdaptadorDesembolsoStub` (`app/infrastructure/pagos.py`), es un stub sustituible: solo registra el desembolso en memoria, sin red de pagos real. Sustituir el stub por una pasarela real (p. ej. `ms-pagos`) no requiere cambiar `application/` ni `domain/`, solo cumplir el `Protocol`. El pago es idempotente por `evento_id` (`UNIQUE` en `pago_parametrico.evento_id`): reprocesar el mismo evento no genera un segundo desembolso, se conserva el original. Al pagar, el siniestro transiciona a `pagado` usando la máquina de estados de HU-30, con monto y marca de tiempo persistidos en `pago_parametrico`.

### Siniestro asistido (HU-157) — aprobación asíncrona

Lectura del enunciado que aplica: §2.2 "pago de siniestros de **bajo monto** de forma automática"; §5.1 #3 "se evalúa, se aprueba y se paga **o se enruta a un perito**"; §6.4 / `EC-SEG-08` el caso marcado por el antifraude queda **retenido con traza**. No hay meta de latencia para aprobar (solo para consultar el estado), así que la decisión es asíncrona:

```
POST /v1/siniestros (multipart)  ->  S3 + siniestro RECIBIDO  ->  201 al instante
worker (cada WORKER_INTERVALO_SEGUNDOS, FOR UPDATE SKIP LOCKED)
  -> EN_EVALUACION -> motor de reglas (app/domain/motor_reglas.py)
       aprobado  -> DECIDIDO[aprobado] -> pago stub idempotente -> PAGADO   (sin humano)
       rechazado -> DECIDIDO[rechazado]   (póliza no vigente / hecho fuera de vigencia)
       revision  -> EN_EVALUACION + requiere_revision  -> cola del operador
operador: /decision (aprobar|rechazar con motivo) · /perito · /pago (bajo monto, HU-29)
```

- **Motor de reglas** (determinista, sin red, evalúa todas las reglas para la auditoría): `poliza_vigente` y `fecha_en_vigencia` rechazan; `ramo_parametrizado`, `evidencia_adjunta`, `sin_avisos_duplicados` (antifraude, ventana por ramo) y `monto_bajo_umbral` retienen. Si el motor falla, el caso queda retenido (nunca se pierde).
- **Parametría** (`parametro_ramo`): reserva por ramo y umbral de aprobación automática. La reserva nunca supera la suma asegurada. Semilla: `proteccion-dispositivo` 420.000 (bajo el umbral de 500.000, se aprueba solo), `vida-crediticia` 3.200.000 y `soat-motocicleta` 890.000 (van a revisión).
- **Estados**: se conserva el modelo único de HU-30 y se agrega `resultado` (aprobado/rechazado) dentro de `decidido`. Con `aprobado` vale `decidido -> pagado`; `rechazado` es terminal; `en_evaluacion -> enrutado` es el perito. Los paramétricos (sin `resultado`) siguen con la tabla original.
- **Evidencia (N6)**: PNG, JPG, PDF o MP4, máx. 10 MB y 5 archivos. Primero se sube a S3 y después se confirma la transacción: si S3 falla, responde 503 y no queda aviso a medias. La llave es `siniestros/{siniestro_id}/{adjunto_id}` (no usa el nombre del cliente). La tabla `siniestro_adjunto` guarda bucket, llave, tipo, tamaño y SHA-256 ligados al usuario y al siniestro; las URLs de lectura se firman al consultar y expiran (`URL_EVIDENCIA_EXPIRA_SEGUNDOS`).
- **Idempotencia**: `Idempotency-Key` en el alta (un reintento devuelve el mismo aviso con 200) y clave determinista del pago (un reintento devuelve el mismo comprobante y queda en `pago_siniestro_intento` como `reintento_idempotente`).
- **Seguridad**: todas las rutas exigen el JWT que reenvía el BFF (`SOLVENTA_TOKEN_SECRET`). Solo un `cliente` avisa y solo a su nombre (`usuario_id` del cuerpo = `uid` del token); el cliente solo lista y consulta lo suyo (ajeno -> 404); decidir, perito, pago y forzar el motor son solo del `operador`, y la auditoría guarda el `sub` del token como actor.
- **Póliza**: igual que HU-33, ms-siniestros no llama a ms-polizas; el BFF envía la foto de la póliza (dueño, vigencia, ramo) en el aviso.
- **Eventos**: `AvisoSiniestroRecibido`, `SiniestroDecidido`, `SiniestroRetenido` y `PagoSiniestroRealizado` quedan en el outbox para el push de estado (N7) cuando exista el publicador del outbox (N12). El worker no depende de ese publicador.

| Endpoint | Uso |
| --- | --- |
| `POST /v1/siniestros` | Alta multipart: parte `datos` (JSON `AvisoEntrada`) + parte `archivos`. |
| `GET /v1/siniestros?usuario_id=&tipo=&estado=&resultado=&requiere_revision=` | Mis siniestros y chips de la cola. Sin filtros: lista completa (comportamiento previo). |
| `GET /v1/siniestros/{id}/detalle[?usuario_id=]` | Detalle con evidencia firmada, decisiones auditadas, pago, intentos y `clave_pago`. |
| `POST /v1/siniestros/{id}/decision` · `/perito` · `/pago` | Acciones del operador (HU-27/28/29). |
| `POST /v1/siniestros/evaluaciones-pendientes` | Fuerza una pasada del motor sin esperar al worker (operación y E2E). |
| `GET /v1/parametros-ramo` | Parametría vigente. |

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
| `S3_EVIDENCIAS_BUCKET` | vacío | Bucket de evidencia. Vacío = almacén en memoria (solo desarrollo). |
| `AWS_REGION` | `us-east-1` | Región del bucket. En EKS las credenciales llegan por IRSA. |
| `S3_ENDPOINT_URL` / `S3_ENDPOINT_PUBLICO` | — | Solo local: endpoint del doble de S3 y el que usa el navegador para las URLs firmadas. |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `S3_CREAR_BUCKET` | — | Solo local (LocalStack). |
| `WORKER_EVALUACION_HABILITADO` / `WORKER_INTERVALO_SEGUNDOS` | `true` / `2.0` | Worker asíncrono del motor. |

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
docker compose up --build          # servicio en :8080 + PostgreSQL 16 con el DDL de db/ + S3 local (LocalStack) en :4566
```

La imagen fija el runtime (`python:3.12.7-slim-bookworm`, nunca `latest`) y corre con un usuario sin privilegios (uid 1000). El puerto 8080 y el uid son los que espera el chart `infra/k8s/charts/microservicio`; con `uvicorn` local sin Docker el servicio sigue en :8000.

## Despliegue

Imagen `runtime` del `Dockerfile` hacia EKS (vista de despliegue §1.1.3). El DDL oficial del servicio está en `db/schema/08_ms_siniestros.sql` (reclamación manual) y `db/schema/13_ms_siniestros_parametrico.sql` (extensión aditiva de HU-30/32/33/34) y `db/schema/14_ms_siniestros_aviso_asistido.sql` (siniestro asistido, HU-157; copia local `db/05_ms_siniestros_aviso_asistido.sql`) del repo; las tablas `reclamacion`/`evidencia_siniestro`/`evaluacion_siniestro` del DDL 08 quedan sin uso; el schema `ms_siniestros` vive en la instancia compartida que provisiona Terraform. Sobre ella se aplican, en orden, los archivos de `db/` de este servicio.
