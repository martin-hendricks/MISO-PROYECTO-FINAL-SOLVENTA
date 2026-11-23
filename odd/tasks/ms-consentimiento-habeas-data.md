# ms-consentimiento — stub de habeas data

> Rama: `feature/ms-consentimiento-habeas-data` · Base: `develop`

## Objetivo

Implementar `apps/backend/ms-consentimiento/` (hoy solo tiene `README.md`, el servicio nunca se implementó) como un **stub explícito** de gestión de consentimiento de habeas data (Ley 1581 colombiana): un servicio interno simple que registra el otorgamiento y la revocación de consentimiento por cliente y expone ese dato al resto del backend (`ms-identidad` lo consume) a través de un contrato HTTP fijo, ya acordado con el equipo que construye el lado consumidor en paralelo.

## Problema

- `apps/backend/ms-consentimiento/README.md` dice explícitamente "Pendiente de implementación" y referencia el ASR `EC-SEG-03` (revocación efectiva ≤5 min, propagada vía eventos) como el objetivo final — pero no hay ningún código, ningún esquema de base de datos ni ningún test en el servicio.
- `infra/k8s/values/ms-consentimiento.yaml` ya existe y está completo (`grupoEscalado: "b"`, `externalSecrets.habilitado: false`, variable `MS_IDENTIDAD_URL`), y `infra/terraform/environments/minimo/main.tf` ya contempla `ms_consentimiento` dentro de `module.rds_compartida` — es decir, la infraestructura de despliegue está lista y esperando una imagen que todavía no existe.
- Otro equipo está construyendo en paralelo el lado consumidor del contrato (`ms-identidad` llamando a este servicio), así que el contrato HTTP (rutas, verbos, forma de entrada/salida) quedó fijado de antemano y no se puede cambiar sin romper ese trabajo paralelo.
- Implementar el ASR `EC-SEG-03` completo (propagación de la revocación por eventos en ≤5 minutos a todo el sistema, versionado de política legal real) está fuera del alcance de esta tarea: se construye deliberadamente un stub que resuelve la necesidad inmediata (el dato "¿tiene este cliente consentimiento vigente?") sin la integración legal/de eventos completa, y eso queda documentado explícitamente en el código y el README para que no se confunda con la implementación final.

## Alcance

### Dentro de alcance

- Generar el esqueleto del servicio con `apps/backend/scripts/nuevo-servicio.sh ms ms-consentimiento` (copia `ms-arquetipo`, preserva el `README.md` existente).
- Dominio: entidad `Consentimiento` (`cliente_id`, `otorgado_en`, `revocado_en`, propiedad `vigente`) con la regla "a lo sumo un consentimiento vigente por cliente_id". Sin outbox, sin eventos de dominio: es un stub, no propaga nada.
- Casos de uso async (`otorgar_consentimiento`, `consultar_consentimiento_vigente`, `revocar_consentimiento`) que reciben una UoW inyectada, siguiendo el mismo patrón de `ms-perfilamiento/app/application/casos_uso.py`.
- Puerto `RepositorioConsentimientos` (Protocol) + `UnidadDeTrabajo` (Protocol), repositorio SQL con SQLAlchemy 2 async (`RepositorioConsentimientosSQL`), excepciones de dominio (`ReglaDeNegocioViolada`, `NoEncontrado`) mapeadas a HTTP en `main.py`.
- Contrato HTTP fijo (acordado con el equipo que consume desde `ms-identidad`):
  - `POST /v1/consentimientos` — `{"cliente_id": "..."}`. Idempotente: 201 si crea uno nuevo, 200 si ya había uno vigente.
  - `GET /v1/consentimientos/{cliente_id}` — 200 con el vigente, 404 si no hay ninguno (nunca otorgado o el último revocado).
  - `DELETE /v1/consentimientos/{cliente_id}` — revoca el vigente (200, `vigente: false`), 404 si no había ninguno vigente.
- Esquema de base de datos `ms_consentimiento`, tabla `consentimiento` (`id UUID`, `cliente_id TEXT`, `otorgado_en TIMESTAMPTZ`, `revocado_en TIMESTAMPTZ NULL`) con índice único parcial `WHERE revocado_en IS NULL` para garantizar la regla de "a lo sumo un vigente por cliente", mismo patrón que `ms-perfilamiento/db/01_ms_perfilamiento.sql`.
- `/health/live` y `/health/ready` (el segundo verificando conexión real a la base), siguiendo el patrón ya usado por los microservicios más recientes (`ms-identidad`, `ms-pagos`, `ms-suscripcion`, `ms-polizas`, `notificaciones`) en vez del `/health` único del arquetipo — es el que ya espera `infra/k8s/values/ms-consentimiento.yaml` en sus `probes`.
- Tests unitarios (dominio, casos de uso con doble en memoria, API con `TestClient`) y de integración (marcados `integration`, contra Postgres real) siguiendo el mismo patrón de archivos que `ms-arquetipo`/`ms-perfilamiento`.
- Edición de `apps/backend/docker-compose.yml`: nuevo servicio `db-consentimiento` (mismo patrón que `db-perfilamiento`) y `ms-consentimiento` (puerto `8011:8080`, próximo libre tras `8010` de `ms-identidad`).
- Edición de `infra/scripts/levantar-local.sh`: agregar `ms-consentimiento:db-consentimiento` a la lista `SERVICIOS` y al `docker compose restart` final.
- Documentación explícita del carácter de stub, en el docstring de `Consentimiento` (`app/domain/modelos.py`) y en el `README.md` del servicio.

### Fuera de alcance

- **Propagación de la revocación por eventos en ≤5 minutos (el ASR `EC-SEG-03` real).** Este servicio no tiene outbox ni publica ningún evento de dominio. Revocar solo actualiza la fila en la base; cualquier consumidor debe consultar `GET /v1/consentimientos/{cliente_id}` directamente para enterarse de un cambio. Cerrar el ASR completo requeriría un mecanismo de notificación (outbox + relay + consumidores) que no se construye aquí.
- **Versionado de política/texto legal.** No hay `version_politica`, snapshot del documento aceptado, ni distinción de finalidades de tratamiento — solo el hecho binario "otorgado" / "revocado" con marca de tiempo, para un único tipo fijo (`habeas_data`).
- **Integración con `ms-identidad` o `bff-web`/`bff-movil` del lado consumidor.** Ese trabajo lo hace otro equipo en paralelo contra este mismo contrato; esta tarea solo entrega el servicio que expone el contrato, no modifica a quien lo consume.
- **Terraform** (`infra/terraform/`): ya resuelto, `ms-consentimiento` ya está contemplado en `module.rds_compartida`.
- **`infra/k8s/values/ms-consentimiento.yaml`**: ya existe y está completo, no se tocó.
- **`.github/workflows/*`**: el mecanismo de autodescubrimiento ya recoge el servicio nuevo con solo que exista el `Dockerfile`, no se tocó.
- **Autenticación de usuario final (JWT de cliente).** Es consumo servicio-a-servicio (igual que el resto de `ms-*` del núcleo, ver `ms-arquetipo/README.md`): no valida ningún token de cliente, se asume que el borde (BFF) ya resolvió la autenticación antes de llegar aquí.

## Tareas

| ID | Tarea | Ruta | Evidencia |
| --- | --- | --- | --- |
| T-01 | Generar el esqueleto con `scripts/nuevo-servicio.sh ms ms-consentimiento`; confirmar que preserva el `README.md` original. | `apps/backend/ms-consentimiento/` | `git diff` del README muestra el contenido original intacto + sección "Desarrollo" del arquetipo añadida. |
| T-02 | Dominio: `Consentimiento` (otorgar/revocar/vigente) con el aviso explícito de stub en el docstring. | `app/domain/modelos.py`, `app/domain/errores.py` | `tests/test_dominio.py`, 6 tests. |
| T-03 | Puerto de persistencia (Protocol) sin outbox. | `app/ports/persistencia.py` | Revisión de código: sin `Outbox`/`EventoDominio`. |
| T-04 | Casos de uso: otorgar (idempotente), consultar vigente, revocar. | `app/application/casos_uso.py` | `tests/test_casos_uso.py`, 8 tests con doble en memoria (`tests/dobles.py`). |
| T-05 | Repositorio SQL (SQLAlchemy 2 async) + esquema `ms_consentimiento`. | `app/infrastructure/sql.py`, `db/01_ms_consentimiento.sql` | `tests/test_mapeo_sql.py` (fechas tz-aware), `tests/test_repositorio_sql.py` (2 tests de integración, verificados contra Postgres real en Docker). |
| T-06 | Rutas HTTP del contrato fijo + mapeo de errores de dominio a HTTP en `main.py`. | `app/api/v1/rutas.py`, `app/api/v1/schemas.py`, `app/main.py` | `tests/test_api.py`, 10 tests end-to-end vía `TestClient`. |
| T-07 | `/health/live` + `/health/ready` (con chequeo real de conexión a BD), alineado con lo que ya espera `infra/k8s/values/ms-consentimiento.yaml`. | `app/observabilidad.py` | `tests/test_api.py::test_health_metrics_y_correlacion`; verificado también con `curl` contra el contenedor Docker real. |
| T-08 | Documentar el alcance de stub en el `README.md` del servicio (sección "Alcance real de esta implementación: STUB explícito" + tabla del contrato HTTP). | `apps/backend/ms-consentimiento/README.md` | Lectura del archivo. |
| T-09 | Agregar `db-consentimiento` + `ms-consentimiento` (puerto `8011:8080`) al compose compartido. | `apps/backend/docker-compose.yml` | `docker compose config --quiet` sin errores; `docker compose up -d --build db-consentimiento ms-consentimiento` levantó ambos contenedores sanos. |
| T-10 | Agregar el servicio a la lista de `levantar-local.sh`. | `infra/scripts/levantar-local.sh` | Revisión de código: `ms-consentimiento:db-consentimiento` en `SERVICIOS` y en el `restart` final. |
| T-11 | Smoke test manual de los 3 endpoints contra el contenedor Docker real. | — | Ver "Criterios de aceptación" más abajo para la evidencia completa de cada llamada. |

## Criterios de aceptación

1. `cd apps/backend/ms-consentimiento && python -m pytest tests -m "not integration and not contract" --allow-hosts=127.0.0.1,::1 --cov` pasa en verde. **Verificado: 26 passed, 86% cobertura** (tanto en el entorno local como dentro de la imagen Docker `--target test`).
2. Los 2 tests marcados `integration` pasan contra un Postgres 16 real con el DDL de `db/01_ms_consentimiento.sql` aplicado. **Verificado** (contenedor `postgres:16.4-bookworm` vía el `docker-compose.yml` propio del servicio): confirma que el índice único parcial `uq_consentimiento_vigente_por_cliente` permite revocar y volver a otorgar (nuevo `id`) sin violar la unicidad.
3. `docker compose -f apps/backend/docker-compose.yml up -d --build db-consentimiento ms-consentimiento` levanta ambos contenedores sanos (`db-consentimiento` healthy, `ms-consentimiento` corriendo). **Verificado.**
4. Smoke test manual contra el servicio en Docker (puerto `8011`), con las respuestas exactas:
   - `GET /health/live` → `200 {"status":"ok"}`; `GET /health/ready` → `200 {"status":"ok"}` (conexión real a `db-consentimiento`).
   - `POST /v1/consentimientos {"cliente_id":"cliente-docker-1"}` (primera vez) → `201`, `vigente: true`, `revocado_en: null`.
   - Mismo `POST` otra vez → `200` con el **mismo `id`** (idempotente).
   - `GET /v1/consentimientos/cliente-docker-1` → `200`, mismo registro.
   - `DELETE /v1/consentimientos/cliente-docker-1` → `200`, `vigente: false`, `revocado_en` con marca de tiempo.
   - `GET /v1/consentimientos/cliente-docker-1` (tras revocar) → `404 {"codigo":"no_encontrado", ...}`.
   - `DELETE /v1/consentimientos/cliente-docker-1` (otra vez) → `404`.
   - `GET /v1/consentimientos/cliente-nunca` (cliente que nunca otorgó) → `404`.
   
   Todas verificadas con `curl` reales contra el contenedor — ver reporte de la sesión de implementación.
5. El carácter de stub queda documentado explícitamente en al menos dos lugares: el docstring de `Consentimiento` en `app/domain/modelos.py` y la sección "Alcance real de esta implementación: STUB explícito" del `README.md` del servicio — ambos nombran puntualmente qué NO cubre (propagación por eventos ≤5 min del ASR `EC-SEG-03`, versionado de política legal).
6. No se modificó ningún archivo de `infra/terraform/`, `infra/k8s/values/ms-consentimiento.yaml` ni `.github/workflows/*`.
7. El contrato HTTP implementado coincide exactamente con el acordado (rutas, verbos, nombres de campos, códigos de estado) para no romper el trabajo paralelo del equipo que lo consume desde `ms-identidad`.
