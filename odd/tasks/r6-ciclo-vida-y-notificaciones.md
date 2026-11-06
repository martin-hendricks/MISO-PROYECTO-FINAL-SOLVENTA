# R6 · Ciclo de vida, avisos, reportes y notificaciones

> Rama: `feature/r6-ciclo-vida-y-notificaciones` · Base: `develop` (`5b197ac`, 2026-11-06)
> Insumo: wiki `analisis-final/analisis-flujos-faltantes.md` (corte 2026-11-02, `22a785d`) + PDF §5.1-6, §5.2.
> Responsable del flujo: R6 (B5). Alcance aprobado: **Fase 1 MVP + Fase 2 post-MVP**, avisos con **N20 real**, reportes con **externo mockeado**.

## Objetivo

Cerrar el recorrido R6 de punta a punta: el operador y el cliente gestionan el ciclo de vida de la póliza (renovar, modificar, cancelar, autoservicio), el sistema avisa vencimientos y renovaciones por web y móvil, y se generan los reportes al regulador y a la reaseguradora. Las notificaciones se disparan por eventos de dominio (`:BusEventos`) a través de un servicio de notificaciones propio.

## Contexto y por qué

La wiki marcó R6 en 🟡 con corte `22a785d`. Desde entonces entraron:

- **PR #138** (2026-11-02 03:17 UTC): HU-59 renovar + HU-61 cancelar + sección `polizas` del back-office, completos y con E2E activos.
- **PR #136** (2026-11-03): UI móvil de avisos de vigencia (HU-159), con datos mock.
- **PR #158** (2026-11-06): preferencia de renovación automática (solo flag; no renueva ni cobra).

Por eso **no se reimplementa** lo de #138/#136/#158. Lo que falta de verdad es: UI de modificar coberturas (HU-60), avisos web (HU-119/120), datos reales de avisos móviles (HU-64/65), reportes (HU-62/63), N20 (notificaciones + push) y N12 (publicador del outbox). Después, Fase 2: HU-66..69.

## Decisiones tomadas (2026-11-06)

1. Alcance: **Fase 1 + Fase 2 post-MVP**.
2. Avisos: **N20 con push real**, validando no pisar el trabajo de los compañeros.
3. Reportes: flujo real interno, **adaptador externo mockeado** (mismo patrón que `PasarelaStub` / `FirmaStub`).
4. Orden: validar paralelización; se construye primero lo que no colisiona con PRs abiertos.
5. Push externo: FCM/APNs **no tienen credenciales** en el proyecto. Se implementa el puerto y un adaptador stub determinista; el envío real queda listo para conectar cuando existan credenciales.

## Alcance autorizado

- `apps/backend/ms-notificaciones/` (nuevo)
- `apps/backend/outbox-relay/` (nuevo; N12)
- `apps/backend/ms-polizas/` (avisos por vencer + reportes + migración `05_*`)
- `apps/backend/bff-web/` (routers nuevos de avisos y reportes; UI de HU-60)
- `apps/backend/bff-movil/` (avisos reales + registro de token)
- `apps/web/` (back-office: avisos, reportes, modificar coberturas; autoservicio y tableros de Fase 2)
- `apps/mobile/` (avisos reales, push, navegación)
- `infra/k8s/values/` (notificaciones, outbox-relay, analitica)
- `db/schema/` (si hace falta alinear el esquema canónico)
- `odd/tasks/` (este documento)

## Fuera de alcance

- Credenciales y cuentas reales de FCM/APNs, regulador o reaseguradora.
- Reimplementar HU-59/HU-61 (#138) o la preferencia de renovación (#158).
- Cambiar reglas de negocio de suscripción, emisión o siniestros.
- Tocar `feature/HU-157-...`, `feature/r5-vida-hipotecario` ni sus archivos compartidos sin integrar antes.

## Mapa de colisiones con PRs abiertos

| Archivo caliente | PR abierto que lo toca | Estrategia |
| --- | --- | --- |
| `bff-web/app/main.py` | #161, #164 | Registrar routers nuevos con una sola línea; resolver conflicto al integrar. |
| `bff-web/app/routers/operador.py` | #161, #164 | **No editar**: crear `routers/ciclo_vida.py` y `routers/reportes.py`. |
| `bff-web/app/routers/cliente.py` | #160, #162 | Evitar hasta que mergeen; si se necesita, cambio quirúrgico. |
| `bff-movil/app/main.py` | #160, multirramo residual | Registrar router nuevo; conflicto de una línea. |
| `bff-movil/.../cliente.py` | #160, multirramo residual | Reemplazar el mock de `/avisos` solo después de #160. |
| `apps/web/src/app/app.routes.ts` | #160, #161, #162, #164 | Añadir rutas al final; resolver conflicto al integrar. |
| `apps/web/src/app/core/i18n/*.json` | #160, #161 | Añadir claves nuevas; conflicto aditivo. |
| `apps/mobile/.../RemoteRepositories.kt`, `CustomerNavHost.kt`, `SolventaRoute.kt`, `strings.xml` | #160 | Diferir la UI móvil hasta integrar #160. |
| `apps/backend/ms-polizas/` | ninguno | Seguro. |
| `apps/backend/ms-notificaciones/`, `outbox-relay/` | ninguno (nuevos) | Seguro y paralelizable. |

## Paralelización

- **Sí** se puede paralelizar la **lectura/exploración** y la **verificación**.
- **No** conviene ejecutar varios escritores sobre el mismo árbol: los puntos calientes (`main.py`, `app.routes.ts`, i18n, navegación móvil) se pisan.
- Plan recomendado:
  - **Track A (seguro ahora)**: `ms-notificaciones` + `outbox-relay` + `ms-polizas` (archivos nuevos o sin PR abierto).
  - **Track B (tras mergear #161/#164)**: `bff-web` + web back-office (avisos, reportes, HU-60 UI).
  - **Track C (tras mergear #160)**: `bff-movil` + mobile (avisos reales, push, navegación).
- Si se autorizan worktrees aislados, A/B/C pueden correr en paralelo y integrarse en este orden. Sin esa autorización, se escribe secuencial y se paraleliza solo la verificación.

## Criterios de aceptación

1. `ms-notificaciones` arranca, expone `/health/live`, `/health/ready`, registra dispositivos, lista notificaciones por usuario y las marca leídas. Tests unitarios verdes.
2. El consumidor de `BusEventos` convierte `PolizaEmitida/Renovada/Modificada/Cancelada` en notificaciones idempotentes (`UNIQUE(evento_origen_id, canal)`) y llama al adaptador de push una sola vez por evento/canal.
3. `outbox-relay` publica los eventos pendientes de los esquemas de los productores y actualiza `publicado_en`; reintenta sin duplicar.
4. `ms-polizas` expone pólizas por vencer (ventana configurable) y reportes regulador/reaseguradora con adaptador externo stub; tests de API y dominio.
5. `bff-web` expone avisos de vencimiento/renovación y reportes al operador, con autorización de rol; la UI del back-office deja de ser placeholder.
6. El detalle de póliza del back-office permite modificar coberturas (nombre, suma asegurada, deducible) y refleja el resultado; E2E `modification` deja de estar `@pendiente`.
7. `bff-movil` sirve avisos reales (sin `POL-88219-CO` hardcodeado) y registra el token de push; la app muestra la lista y el detalle.
8. Fase 2: autoservicio web, orquestador de ciclo de vida, eventos de analítica y tableros/SLAs con datos reales y pruebas.
9. `pytest -m "not integration and not contract"` verde en cada servicio tocado; `pnpm test` y `pnpm e2e` verdes en web; `./gradlew :app:createDebugUnitTestCoverageReport` verde en móvil.
10. No se rompe ningún contrato existente ni se duplica lo de #138/#136/#158.

## Verificación

```bash
# Backend (por servicio tocado)
cd apps/backend/<servicio> && pytest -m "not integration and not contract" --allow-hosts=127.0.0.1,::1

# Contratos
python apps/backend/scripts/verify_contracts.py

# Web
cd apps/web && pnpm test && pnpm e2e

# Móvil
cd apps/mobile/Solventa && ./gradlew :app:createDebugUnitTestCoverageReport
```

## Tareas

| ID | Tarea | Ruta | Disparador | Estado |
| --- | --- | --- | --- | --- |
| WU-01 | Generar `ms-notificaciones` desde `ms-arquetipo`; esquema DB; health; config; README. | delegado (writer) | 2+ archivos nuevos | pendiente |
| WU-02 | Endpoints de dispositivos y notificaciones + seguridad + tests. | delegado (writer) | 2+ archivos | pendiente |
| WU-03 | Puerto de push + adaptador stub + tests. | delegado (writer) | prepara escritura | pendiente |
| WU-04 | Consumidor MSK (`aiokafka` + IAM) idempotente + tests con doble. | delegado (writer) | 4+ archivos / infra | pendiente |
| WU-05 | `outbox-relay` (N12): polling, publicación, `publicado_en`, tests. | delegado (writer) | servicio nuevo | pendiente |
| WU-06 | `ms-polizas`: pólizas por vencer + reportes + migración `05_*` + tests. | delegado (writer) | 2+ archivos | pendiente |
| WU-07 | `bff-web`: routers `ciclo_vida` y `reportes`; registrar en `main.py`; tests. | delegado (writer) | 2+ archivos | pendiente |
| WU-08 | Web back-office: sección `avisos` real + `reportes` + HU-60 UI + i18n + E2E. | delegado (writer) | 4+ archivos | pendiente |
| WU-09 | `bff-movil`: avisos reales + token push; retirar mock; tests. | delegado (writer) | 2+ archivos | pendiente |
| WU-10 | Mobile: lista/detalle de avisos, push, navegación, strings, tests. | delegado (writer) | 4+ archivos | pendiente |
| WU-11 | Fase 2 · HU-66 autoservicio web. | delegado (writer) | 2+ archivos | pendiente |
| WU-12 | Fase 2 · HU-67 orquestador de ciclo de vida. | delegado (writer) | 2+ archivos | pendiente |
| WU-13 | Fase 2 · HU-68 eventos de analítica (`ms-analitica` o consumidor). | delegado (writer) | servicio nuevo | pendiente |
| WU-14 | Fase 2 · HU-69 tableros y SLAs. | delegado (writer) | 2+ archivos | pendiente |

## Estrategia de entrega

- `delivery_strategy`: `single-pr` (pedido explícito de una sola rama).
- El pronóstico supera ampliamente las ~400 líneas autoradas: se requiere `size:exception` del mantenedor o, si lo prefiere, dividir en PRs encadenados por track (A/B/C). Queda pendiente de su decisión al abrir el PR; no bloquea la construcción.
- Cada tarea cierra con al menos un commit de unidad de trabajo en la rama, con tests y docs.

## Progreso

- [x] Reconciliación wiki vs `develop` (PRs #138/#136/#158 identificados).
- [x] Rama creada desde `develop` actualizado (`5b197ac`).
- [x] WU-01: `apps/backend/notificaciones/` generado desde `ms-arquetipo` (renombrado de `ms-notificaciones`), esquema, health, config, README.
- [x] WU-02: endpoints de dispositivos/notificaciones + seguridad + tests (`app/api/v1/rutas.py`, `app/seguridad.py`).
- [x] WU-03: puerto de push + adaptador stub (`app/ports/push.py`, `app/infrastructure/push_stub.py`), con tests.
- [~] WU-04: consumidor MSK parcial. `app/domain/eventos.py` (contrato `EventoBus`) y `app/application/manejadores.py` (traducción evento→notificación) completos y testeados. `app/infrastructure/kafka_consumer.py` tiene `ConsumidorMSK.procesar_mensaje` (usado por tests) pero el `_bucle` real de consumo contra MSK (líneas 28-31, 55-72, 81-115, cobertura 54%) no está probado ni confirmado contra IAM/aiokafka real. **Bug encontrado y corregido en esta sesión** (2026-11-06): `manejar_evento` devolvía la instancia de `Notificacion` obtenida ANTES de despachar el push, así que el campo `estado` nunca reflejaba `"enviada"`/`"fallida"` en el valor de retorno aunque el despacho sí ocurriera en el almacén — `despachar_notificacion` opera sobre su propia instancia en otra unidad de trabajo y devuelve solo `bool`. Fix: releer la notificación tras despachar. 93/93 tests pasan ahora (antes 91/93), cobertura total del servicio 80% (huecos reales en `kafka_consumer.py` 54%, `sql.py` 47%, `main.py` 62% — infraestructura de integración aún sin probar contra MSK/RDS real).
- [x] WU-05: `outbox-relay` completo. `app/infrastructure/sql.py` (`RepositorioOutboxSQL`: `SELECT ... FOR UPDATE SKIP LOCKED` por esquema, una sola transacción por lote — si `publicador.publicar` falla a mitad de camino, nada queda marcado `publicado_en`, el próximo ciclo reintenta el lote completo). `app/infrastructure/kafka_publicador.py` (`PublicadorMSK`, mismo patrón IAM/OAUTHBEARER que `notificaciones/app/infrastructure/kafka_consumer.py`, productor en vez de consumidor). `app/config.py`: una `DATABASE_URL_MS_*` por esquema (6 variables — `ms_polizas`/`ms_siniestros` tienen RDS propio, el resto comparte `DBCompartida`, confirmado contra `infra/terraform/modules/secrets/main.tf`). `app/main.py` reescrito: ya no es boilerplate HTTP del arquetipo — arranca `bucle_relay` y un servidor FastAPI mínimo (solo `/health`/`/metrics`, reusando `observabilidad.py`) en paralelo vía `asyncio.gather`, con shutdown limpio por `SIGTERM`/`SIGINT`. El chart de Helm exige `httpGet` para los probes, por eso no se pudo quitar FastAPI del todo. `pyproject.toml` renombrado (`ms-arquetipo` → `outbox-relay`), con `aiokafka`/`aws-msk-iam-sasl-signer-python` agregados. Dockerfile runtime cambia a `python -m app.main` (ya no hay `app:app` que uvicorn pueda servir solo). 29/29 tests unitarios + **5/5 tests de integración verificados contra un Postgres real** (`docker run postgres:16.4-bookworm` temporal, confirmó `FOR UPDATE SKIP LOCKED`, la interpolación segura del esquema, y la atomicidad "todo o nada" del lote — encontró y corrigió un bug real del fixture: asyncpg no acepta varios statements DDL en un solo `execute`, a diferencia de psycopg2).
- [ ] WU-06 … WU-14: sin empezar.

## Siguiente paso

Se retomó el 2026-11-06 tras quedarse sin créditos en opencode a mitad de WU-04. Con WU-01 a WU-05 completos (notificaciones + outbox-relay, ambos con tests verdes y persistencia validada contra Postgres real), el flujo de eventos de dominio → push ya no está huérfano. Falta, en orden: (1) validar WU-04 contra un MSK real (o al menos credenciales IAM reales en un ambiente), ya que tanto `ConsumidorMSK` como `PublicadorMSK` solo se probaron con dobles/estado interno, nunca contra un broker real; (2) avanzar a WU-06 (`bff-web`: routers `ciclo_vida`/`reportes`) siguiendo el mapa de colisiones del plan (no tocar `routers/operador.py`, crear archivos nuevos) una vez que PRs #161/#164 mergeen a `develop`.
