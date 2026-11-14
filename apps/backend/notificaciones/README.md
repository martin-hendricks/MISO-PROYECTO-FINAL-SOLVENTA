# notificaciones

Microservicio del núcleo de Solventa que guarda las **notificaciones al cliente** y los
**dispositivos push** (N20). Expone la consulta y el ciclo de vida al canal (BFF) y deja
listo el puerto de envío para que el consumidor de MSK despache los eventos del bus.

Resuelve el negocio y tiene su propio almacén (schema `notificaciones`). No valida JWT en
el borde por delegación: aquí sí valida el token de acceso porque las rutas son de cliente
y cada llamante solo puede operar sobre sus propios datos.

## Estructura (hexagonal)

```
app/
├── main.py                  crear_app(): lifespan, wiring de motor/UoW/push, errores → HTTP
├── config.py                pydantic-settings (variables de entorno / .env)
├── dependencies.py          raíz de composición: UoW y enviador de push
├── seguridad.py             JWT HS256 (mismo SOLVENTA_TOKEN_SECRET), LlamanteDep, alcance()
├── observabilidad.py        /health, /metrics (Prometheus), X-Correlation-Id
├── api/v1/                  rutas + DTO de /v1/notificaciones
├── domain/                  Notificacion, DispositivoPush y sus transiciones (sin SQL)
├── application/             casos de uso: registro, consulta, lectura y despacho
├── ports/                   persistencia.py y push.py (interfaces, DIP)
└── infrastructure/          SQLAlchemy 2 async y PushStub
db/01_ms_notificaciones.sql  DDL idempotente del schema notificaciones
tests/                       PyTest sin red ni BD (dobles) + integración marcada
```

## Endpoints

Prefijo `/v1/notificaciones`. Todas las rutas exigen `Authorization: Bearer <access token>`
con `typ == "access"` y derivan `usuario_id` del claim `uid`; **nunca** del body ni del query.
Cualquier rol autenticado (`cliente`, `asesor`, `operador`) opera solo sobre lo suyo.

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/v1/notificaciones/dispositivos` | Upsert por `(usuario_id, token)`. 201 la primera vez, 200 si ya existía; reactiva si estaba inactivo. Body `{plataforma, token}` |
| `DELETE` | `/v1/notificaciones/dispositivos` | Body `{token}`. 204 aunque el token no exista. Token vacío: 422 `token_vacio` |
| `DELETE` | `/v1/notificaciones/dispositivos/{dispositivo_id}` | Desactiva el dispositivo del llamante. 204; 404 si no es suyo |
| `GET` | `/v1/notificaciones/audiencia?usuarioIds=` | Operador siempre. Asesor solo si envía `usuarioIds` (máximo 50). 403 en otro caso |
| `POST` | `/v1/notificaciones/difusiones` | Operador. Audiencia `todos` o `usuarios` (1 a 500). 201 `{difusionId, enviadas, fallidas, sinDispositivo}` |
| `GET` | `/v1/notificaciones/difusiones?limite=20&antesDe=` | Operador. Historial, más reciente primero |
| `GET` | `/v1/notificaciones?limite=20&antes_de=<ISO>` | Notificaciones del llamante, `creada_en DESC`. `limite` 1..100; `antes_de` es cursor |
| `POST` | `/v1/notificaciones/{notificacion_id}/leida` | Marca leída (idempotente). 404 si no es suya |
| `GET` | `/v1/notificaciones/{notificacion_id}` | Detalle. 404 si no es suya |

Las notificaciones de póliza las crea el consumidor de MSK a través de `crear_notificacion`
(idempotente por `(evento_origen_id, canal)`). Las difusiones las crea el operador por HTTP.

`PUSH_PROVEEDOR=stub` arranca solo si `MSK_BOOTSTRAP_BROKERS` está vacío. Con brokers, el
proceso exige `PUSH_PROVEEDOR=fcm` y un `FCM_CREDENCIALES_JSON` válido (JSON con
`project_id`). Sin eso, o con JSON inválido, el arranque falla.

## Variables de entorno

| Variable | Default | Uso |
| --- | --- | --- |
| `SERVICE_NAME` | `notificaciones` | Título del servicio |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/solventa` | Almacén propio |
| `DB_POOL_SIZE` | `10` | Conexiones por réplica |
| `LOG_LEVEL` | `INFO` | |
| `SOLVENTA_TOKEN_SECRET` | — (obligatoria) | Secreto HS256 compartido con ms-identidad |
| `PUSH_PROVEEDOR` | `stub` | `stub` o `fcm` |
| `PUSH_STUB_FALLAR` | `false` | Fuerza el camino de fallo del stub |
| `FCM_CREDENCIALES_JSON` | vacío | JSON de la cuenta de servicio de Firebase. Obligatorio si `PUSH_PROVEEDOR=fcm` |
| `MSK_BOOTSTRAP_BROKERS` | vacío | Brokers de MSK. Si está definido, el proveedor no puede ser `stub` |
| `MSK_TOPIC` | `BusEventos` | Tópico del bus |
| `MSK_CONSUMER_GROUP` | `notificaciones` | Grupo del consumidor. En el clúster coincide con el rol IRSA |
| `MSK_AUTH_MECHANISM` | `AWS_MSK_IAM` | Autenticación de MSK |

## Esquema

El DDL de `db/01_ms_notificaciones.sql` es idempotente (`IF NOT EXISTS`). Si el DDL
canónico `db/schema/12_notificaciones.sql` ya creó la tabla `notificacion`, completa sus
columnas de forma aditiva y sustituye el índice por el compuesto. Crea:

- `notificaciones.notificacion`: `notificacion_id`, `usuario_id`, `evento_origen_id`,
  `canal`, `tipo`, `titulo`, `cuerpo`, `destino`, `estado`, `creada_en`, `enviada_en`,
  `leida_en`, `proveedor_id`; `UNIQUE (evento_origen_id, canal)`.
- `notificaciones.dispositivo_push`: `dispositivo_id`, `usuario_id`, `plataforma`, `token`,
  `activo`, `creado_en`, `actualizado_en`; `UNIQUE (usuario_id, token)`.
- Índices `ix_notificacion_usuario (usuario_id, creada_en DESC)` e
  `ix_dispositivo_usuario (usuario_id, activo)`.

Estados: `pendiente → enviada → leida`, con `fallida` como resultado del envío. Marcar leída
es idempotente. La desactivación de un dispositivo conserva la fila para que un nuevo
registro del mismo token lo reactive.

## Push: adaptador stub

`PushStub` (`app/infrastructure/push_stub.py`) es determinista y no habla con FCM ni APNs:
devuelve `stub-<notificacion_id>`. Con `PUSH_STUB_FALLAR=true` lanza
`ServicioExternoNoDisponible` para probar el camino de fallo. **No hay credenciales reales
en el repositorio.** El adaptador real se conecta cambiando la fábrica en `main.py`
(`app.state.push`) por una implementación del puerto `EnviadorPush`; ni los casos de uso ni
la API cambian.

El consumidor de MSK queda para una tarea posterior: el puerto y
`despachar_pendientes(uow, push, usuario_id=None)` están listos, pero no se arranca ningún
consumidor en el lifespan.

## Desarrollo

**Requisitos:** Python 3.12+ (o solo Docker).

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
export SOLVENTA_TOKEN_SECRET=cambiar-en-local
uvicorn app.main:app --reload                       # http://localhost:8000/docs
```

## Pruebas

```bash
cd apps/backend/notificaciones
pytest -m "not integration and not contract" --allow-hosts=127.0.0.1,::1
```

Las unitarias usan dobles en memoria de la UoW y un push doble: no requieren PostgreSQL ni
red. La suite cubre registro/upsert de dispositivos, listado con paginación y aislamiento por
llamante, lectura idempotente, idempotencia de creación por evento/canal, despacho con éxito
y con fallo, y seguridad JWT (sin token → 401, token ajeno → sin datos).

Integración contra PostgreSQL 16 con el DDL aplicado:

```bash
docker compose up -d db
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/solventa pytest -m integration
```

## Docker

```bash
docker compose up --build          # servicio en :8080 + PostgreSQL 16 con el DDL de db/
docker build --target test -t notificaciones:test . && docker run --rm notificaciones:test
```

La imagen fija `python:3.12.7-slim-bookworm`, instala con `requirements.lock` como
constraints y corre con uid 1000 en el puerto 8080 (chart `infra/k8s/charts/microservicio`).

## Despliegue

Imagen `runtime` hacia EKS. El DDL de referencia compartido es `db/schema/12_notificaciones.sql`;
este servicio lo extiende con `titulo`, `cuerpo`, `destino`, `leida_en`, `proveedor_id` y la
tabla `dispositivo_push` (ver `db/01_ms_notificaciones.sql`).
