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
├── api/v1/              POST /v1/consentimientos, GET/DELETE /v1/consentimientos/{cliente_id}, POST /v1/ofertas-hipotecario,
│                        GET /v1/ofertas-hipotecario/clientes/{cliente_id}/ultima
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

### Oferta competitiva (SOLV-266)

El `ajuste` nunca supera `factor_referencia_mercado` (por defecto `1.10`, variable `FACTOR_REFERENCIA_MERCADO`; valor académico, no es una fuente real de mercado). Cuando el perfil lo supera, la oferta lleva el factor interno `{"factor": "ajuste_competitivo", "impacto": "reduce_prima", "peso": <referencia>}` y el ajuste queda en la referencia. El tope viaja dentro de `factores`, así que `factor_ajuste` se reconstruye igual desde lo persistido y ms-cotizacion cotiza con el mismo valor topado.

### Perfil de riesgo para ms-cotizacion (`IPerfilRiesgo`)

La oferta expone `factor_ajuste` (el `ajuste` de la fórmula, recalculado desde los factores y el snapshot persistidos). `GET /v1/ofertas-hipotecario/clientes/{cliente_id}/ultima` devuelve la oferta más reciente del cliente sin volver a llamar a los adaptadores; ms-cotizacion la lee para cotizar `vida-hipotecario` con este mismo perfil, de modo que la prima cotizada y cobrada en la emisión sale del perfil que el cliente vio explicado. Exige consentimiento vigente (`403` si se revocó) y responde `404` si el cliente aún no tiene ofertas.

### Originación hipotecaria (HU-53, HU-105)

Una originación guarda el crédito para el que el cliente pide vida hipotecario: `valor`, `plazo_meses` y `origen` (`cliente` cuando cotiza en el portal, `socio` cuando la envía un banco aliado). Hay a lo sumo una pendiente por cliente.

| Método | Ruta | Efecto |
| --- | --- | --- |
| `POST` | `/v1/originaciones` | Registra la originación; si ya había una pendiente, la cierra y la reemplaza (`201`) |
| `GET` | `/v1/originaciones/clientes/{cliente_id}/pendiente` | Devuelve la pendiente o `404` |
| `DELETE` | `/v1/originaciones/clientes/{cliente_id}/pendiente` | La cierra al emitir la póliza (`204`, idempotente) |

La tabla se crea con `db/02_ms_perfilamiento_originacion.sql`. Una base creada antes de ese script no lo corre sola: hay que recrear el volumen o aplicarlo a mano.

## Degradación (HU-56)

Cada adaptador tiene su propio timeout (`timeout_open_finance_ms`, `timeout_open_data_ms`, 400ms por defecto) aplicado con `asyncio.wait_for` en `app/application/casos_uso.py`. Si expira o el adaptador lanza cualquier excepción, el atributo correspondiente se sustituye por su valor de respaldo (constante configurable) y se marca `degradado=True` para ese atributo; la `Oferta` resultante expone `degradado=true` si al menos uno de sus atributos vino del respaldo. La oferta degradada sigue siendo válida y se persiste junto con el snapshot completo de insumos (`snapshot_atributos`), para que la decisión de precio sea 100% reconstruible aunque las reglas cambien después.

Cada atributo del snapshot registra qué adaptador respondió (`origen`) y cómo: `estado`, `modo` (`LIVE`, `CACHE` o `DEFAULT`) y `causa` (`timeout` o `fallo` cuando el adaptador no respondió a tiempo). El evento `OfertaHipotecarioEmitida` resume lo mismo por fuente en `fuentes`.

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
| `REDIS_CACHE_OD_HOST` | vacío | Host de `:CacheOD`/`:CacheOF` (HA-03/HA-04). Vacío desactiva la caché |
| `REDIS_CACHE_OD_PORT` | `6379` | Puerto de la caché |
| `REDIS_CACHE_OD_TTL_SECONDS` | `600` | Vigencia fresca de los atributos OF/OD en caché. Pasada, el perfil se considera vencido y toca refrescarlo, pero sigue sirviendo de respaldo |
| `REDIS_CACHE_OD_TTL_DURO_SECONDS` | `86400` | Vigencia máxima: pasada, el perfil desaparece de Redis |
| `PRESUPUESTO_RESPUESTA_MS` | `120` | Lo que una petición espera al proveedor antes de responder con el valor vencido; la invocación sigue en segundo plano |
| `TIMEOUT_PROVEEDOR_MS` | `700` | Timeout de la invocación al proveedor, también la que corre en segundo plano |
| `INTERRUPTOR_VENTANA_S` / `_UMBRAL_TASA` / `_MIN_MUESTRAS` / `_APERTURA_S` | `10` / `0.5` / `10` / `5` | Circuit breaker por tasa de fallo sobre una ventana deslizante |
| `REDIS_CACHE_OD_PASSWORD` | vacío | Token de autenticación. ElastiCache lo exige; el Redis del compose local no |
| `REDIS_CACHE_OD_SSL` | `false` | TLS hacia la caché. ElastiCache lo exige (`transit_encryption_enabled`); el compose local no |
| `TIMEOUT_CACHE_ARRANQUE_MS` | `2000` | Tiempo máximo del PING de arranque y de cada conexión que se abre al calentar el pool. Si falla solo se registra una advertencia y la caché sigue activa |
| `REDIS_CACHE_OD_POOL_CALENTAMIENTO` | `8` | Conexiones que se dejan abiertas al arrancar. Una conexión nueva cuesta decenas de milisegundos, más que `TIMEOUT_CACHE_MS`: sin esto, la primera operación de cada conexión nueva expira y esa petición se queda sin caché. Con TLS, todas las conexiones del pool comparten un único contexto SSL (`redis-py` crea uno por conexión, unos 70 ms de CPU que además bloquean el event loop) |
| `REDIS_CACHE_OD_POOL_MAX` | `32` | Tope de conexiones por réplica. Pasado el tope la operación falla y se salta la caché |
| `REDIS_CACHE_OD_HEALTH_CHECK_S` | `30` | Cada cuánto una conexión inactiva se verifica antes de usarla. También se activa el keepalive de TCP |
| `TIMEOUT_CACHE_MS` | `50` | Tiempo máximo de lectura/escritura en caché; si se excede o falla, se consulta al proveedor |

## Estrategia de caché y resiliencia

Con `REDIS_CACHE_OD_HOST` definido, cada fuente (Open Finance y Open Data) se envuelve en `AdaptadorResiliente` (`app/infrastructure/resiliencia.py`):

1. **Perfil fresco** (menos de `REDIS_CACHE_OD_TTL_SECONDS`): sale de Redis, sin llamar al proveedor.
2. **Perfil vencido o ausente:** se invoca al proveedor con un presupuesto de `PRESUPUESTO_RESPUESTA_MS`. Si responde a tiempo se usa y se guarda. Si no, se responde con el perfil vencido (si lo hay) y la invocación sigue en segundo plano hasta `TIMEOUT_PROVEEDOR_MS` para repoblar la caché. Sin ningún valor guardado el adaptador lanza la excepción y el caso de uso degrada al valor de respaldo, como antes.
3. **Circuit breaker** por tasa de fallo sobre una ventana deslizante: abierto, ni se invoca al proveedor. Pasado `INTERRUPTOR_APERTURA_S` deja pasar una sola sonda.
4. **Coalescencia:** las peticiones concurrentes por la misma cédula comparten una sola invocación.
5. **Revocación de consentimiento:** además de la memoria local, borra de Redis lo guardado bajo ese consentimiento (un conjunto por consentimiento indexa las claves). Como lo vencido se conserva hasta 24 h, esto es obligatorio.

Cada atributo del snapshot queda trazado: `modo=LIVE` si vino del proveedor, `modo=CACHE` si salió de Redis, y `causa` (`timeout` o `fallo`) cuando se sirvió un valor vencido. Sin Redis configurado el comportamiento no cambia: ni caché ni circuit breaker.

Métricas en `/metrics`: `perfilamiento_cache_lecturas_total`, `perfilamiento_cache_errores_total`, `perfilamiento_proveedor_llamadas_total`, `perfilamiento_respaldos_total`, `perfilamiento_circuito_transiciones_total` y `perfilamiento_coalescidas_total`, todas con la etiqueta `fuente` (`of` u `od`).

## Pruebas

```bash
pytest -m "not integration and not contract" --cov           # unitarias: sin BD ni red
```

Integración contra un PostgreSQL 16 con el DDL de `db/` aplicado:

```bash
docker compose up -d db                                      # PostgreSQL local con el DDL de db/
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/solventa pytest -m integration
```

Integración contra un Redis real (ida y vuelta con TTL, la caché evitando la segunda llamada al proveedor, el perfil vencido cuando el proveedor cae, la purga por consentimiento y el PING de arranque). Se saltan solas si no hay Redis:

```bash
docker run -d --name redis-test -p 6390:6379 redis:7.4.2-bookworm
docker run -d --name redis-test-auth -p 6391:6379 redis:7.4.2-bookworm redis-server --requirepass secreto-local
REDIS_TEST_HOST=localhost REDIS_TEST_PORT=6390 \
REDIS_TEST_AUTH_HOST=localhost REDIS_TEST_AUTH_PORT=6391 REDIS_TEST_AUTH_PASSWORD=secreto-local \
  pytest -m integration tests/test_cache_redis_real.py
```

TLS también se prueba en local con un certificado autofirmado:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout /tmp/tls/k.pem -out /tmp/tls/c.pem -days 1 -subj "/CN=localhost"
docker run -d --name redis-test-tls -p 6392:6379 -v /tmp/tls:/tls:ro redis:7.4.2-bookworm \
  redis-server --port 0 --tls-port 6379 --tls-cert-file /tls/c.pem --tls-key-file /tls/k.pem \
  --tls-ca-cert-file /tls/c.pem --tls-auth-clients no --requirepass secreto-tls
REDIS_TEST_TLS_HOST=localhost REDIS_TEST_TLS_PORT=6392 REDIS_TEST_TLS_PASSWORD=secreto-tls \
  pytest -m integration tests/test_cache_redis_real.py
```

Lo que no se puede probar en local es el certificado de Amazon y el token de ElastiCache: eso se valida al desplegar, con el PING de arranque (`cache redis conectada` en el log; si no responde, el servicio sigue arriba y registra una advertencia).

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
