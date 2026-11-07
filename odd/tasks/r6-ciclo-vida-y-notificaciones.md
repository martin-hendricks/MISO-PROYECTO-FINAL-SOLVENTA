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
- [x] **Reconciliación de alcance (2026-11-06):** PRs #161 (HU-157) y #164 ya mergeados a `develop` antes de seguir. #161 construyó una cola de avisos completa para **siniestros** en `bff-web/app/routers/siniestros.py` (`router_operador`: `/avisos`, `/avisos/{id}`, `/avisos/decision`, `/avisos/{id}/perito`, `/avisos/{id}/pago`) — esto NO es lo mismo que los avisos de **vencimiento/renovación de póliza** (HU-119/HU-120) que WU-06/WU-07 todavía debían construir; se confirmó que no hay duplicación. PRs abiertos #160/#165/#166 tocan `asesor.py`/`cliente.py`/`app.routes.ts`/i18n — ninguno toca `main.py`, `operador.py`, `siniestros.py`, ni `ms-polizas`, así que WU-06/WU-07 no tuvieron colisión real. Rama rebaseada limpia sobre `origin/develop`.
- [x] WU-06: `bff-web` — avisos de vencimiento (HU-119) y reportes regulador/reaseguradora (HU-62/HU-63). `app/routers/avisos_poliza.py` (`GET /cliente/polizas/por-vencer`, rol cliente). HU-120 (confirmación de renovación) no necesitó endpoint propio: `GET /cliente/polizas/{numero}` ya refleja `fin_vigencia` actualizada tras renovar. `app/routers/reportes.py` (`GET /operador/reportes/{regulador,reaseguradora}`) — los roles `compliance`/`operations` del Gherkin no existen en el sistema (`ROLES = ("cliente","asesor","operador")`), ambos se autorizan contra `"operador"`. **Bug real encontrado y corregido**: `GET /cliente/polizas/por-vencer` daba 404 porque Starlette prioriza los routers por orden de `include_router`, no por especificidad de patrón — el router de `cliente.py` (con `/polizas/{numero}`, patrón dinámico) capturaba `por-vencer` como `numero` al estar incluido antes. Fix: registrar `avisos_poliza`/`reportes` antes de `cliente`/`operador`. No se tocó `asesor.py`/`cliente.py` (PRs #160/#165/#166 abiertos). 131/131 tests (antes 119), 1 skipped (contrato), 96% cobertura.
- [x] WU-07: `ms-polizas` — mismo alcance, lado servidor. `GET /v1/polizas/por-vencer` (reusa `VENTANA_GRACIA_DIAS` como ventana por defecto en vez de inventar un segundo número mágico; mismo problema de precedencia de rutas que WU-06, resuelto igual: registrado antes de `/{poliza_id}`). Puerto+adaptador `GeneradorReportes`/`ReportesStub` (mismo patrón que `FirmaStub`: determinista, CSV en memoria, nunca I/O real contra SFC/ACORD). `GET /v1/reportes/{regulador,reaseguradora}`, autorizados contra `"operador"` (misma decisión que WU-06 sobre los roles `compliance`/`operations` inexistentes). El reporte a la reaseguradora se limita a pólizas canceladas con su devolución estimada — el único dato de "cartera/siniestralidad" disponible en este servicio, que no tiene acceso a siniestros reales. Contrato verificado exacto contra lo que `bff-web/app/clients/ms_polizas.py` ya esperaba (mismos nombres de query params, misma forma de respuesta) — sin ajustes necesarios de ningún lado tras integrarlos. 169/169 tests (antes 140), 97% cobertura; los 3 métodos SQL nuevos verificados también contra un Postgres real en Docker, no solo con el doble en memoria.
- [x] WU-08: web — `apps/web/src/app/features/backoffice/reportes/` (gateway/viewmodel/vista, rol `operador`, mismo patrón que `features/backoffice/polizas/`; registrado en `sections.ts`/`app.routes.ts`/i18n) para HU-62/HU-63. **Hallazgo de alcance**: `notices.feature` (HU-119/HU-120) dice explícitamente "the customer sees..." — es portal **cliente**, no back-office, a diferencia de lo que el plan original asumía; se corrigió sobre la marcha en vez de construir mal. Avisos de vencimiento (HU-119) resueltos en `apps/web/src/app/features/polizas/avisos/` (portal cliente, mismo patrón que `polizas-lista`), consumiendo `GET /cliente/polizas/por-vencer` ya comiteado en WU-06. HU-120 (confirmación de renovación) se dejó `@pendiente`: ya cubierta por `renewal.feature` con otro texto de step, evita duplicar la misma aserción. **2 bugs reales encontrados y corregidos al correr la suite e2e completa** (no solo los specs nuevos): (1) un step nuevo colgaba 15s por una carrera con la navegación automática post-login a `/inicio`, resuelto con el mismo patrón ya usado en `openAsCustomer`; (2) **regresión preexistente** — el commit de reportes agregó una 5ª sección al back-office pero no actualizó `backoffice.steps.ts`/`.page.ts`, que seguían afirmando "cuatro secciones", rompiendo 3 escenarios e2e que no tenían nada que ver con reportes. Karma: 398/398, 100% cobertura (4 ejes). **E2E completo contra un dev server real (no solo mocks): 39/39 escenarios pasan**, validado en browser real.
- [x] **PR #160 mergeado (2026-11-06) y rama rebaseada.** Resultas: `feature/r5-vida-hipotecario` terminó siendo sobre cotización/perfilamiento/web (`ms-cotizacion`, `ms-perfilamiento`, `apps/web/features/vida-crediticia/`), **nunca tocó `bff-movil` ni `apps/mobile`** — el bloqueo de archivo para WU-09/WU-10 que el plan original anticipaba contra este PR nunca existió realmente. Sí trajo un cambio de diseño real a reconciliar: `infra/k8s/values/bff-movil.yaml` cambió el secreto JWT de `bff-movil` de uno propio (`solventa-minimo-bff-movil-token`, decisión tomada antes en esta sesión) a **reusar el de `bff-web`** (`solventa-minimo-bff-web-token`) — el comentario nuevo documenta que un secreto propio causaba 401 real en `GET /cliente/polizas`, porque `ms-polizas`/`ms-cotizacion`/`ms-identidad`/`ms-siniestros` verifican el JWT que el BFF reenvía con la clave de bff-web; un secreto independiente rompía esa verificación cruzada. Conflicto real de rebase en 2 archivos de soporte e2e (`apps/web/e2e/support/doubles/bff.ts`, `world.ts`) — ambas ramas agregaron un tipo/página nueva en el mismo punto (`MortgageOffer`/`vidaCrediticia` de #160, `PolicyNotice`/`polizasAvisos` de WU-08); resuelto fusionando ambos. Verificado post-rebase: `apps/web` 428/428 (100% cobertura, subió de 398 por los tests propios de #160), `bff-web` 152/152 (subió de 131), `ms-polizas` 159/159 intacto.
- [x] **WU-09/WU-10 construidos deliberadamente ANTES de que #165 mergee** (decisión explícita del usuario: "hazlos y luego resolvemos conflictos"), en paralelo real, sin colisión entre sí (`apps/backend/bff-movil/` vs `apps/mobile/`).
  - **WU-09** (`bff-movil`): `GET /avisos` real (`if es_v1(request)`, mismo patrón que `billetera`/`detalle`) llama a `ms-polizas/v1/polizas/por-vencer` vía un método nuevo en `ClienteNucleo`; `POST /avisos/token` reenvía el registro al servicio `notificaciones` real (`POST /v1/notificaciones/dispositivos`), reusando el mecanismo ya existente de reenvío de JWT (`token_saliente`) — sin segunda clase de cliente HTTP. **Bug de infra real encontrado y corregido**: `infra/k8s/values/notificaciones.yaml` tenía `externalSecrets.habilitado: false` — el servicio nunca iba a recibir `SOLVENTA_TOKEN_SECRET`, cualquier llamada autenticada (incluida la de bff-movil) habría fallado con 500. El contrato real de `/avisos` solo devuelve `tipo: "vencimiento"` (`ms-polizas/por-vencer` no expone confirmaciones de renovación) — consistente con que HU-120 ya quedó `@pendiente` en WU-08. 67/67 tests (antes 60), 96% cobertura.
  - **WU-10** (mobile): el repositorio remoto (`RemoteNoticeRepository`) ya llamaba a `/avisos` real desde el PR #136 — el hardcode real estaba en el **dominio** (`OpenValidityNotice.kt`): exigía `poliza == "POL-88219-CO"` para hacer match, así que con cualquier póliza real de un usuario real nunca encontraba el aviso aunque el backend ya respondiera uno. Generalizado: `reading()` ahora matchea por `tipo`/`estado` sin exigir una póliza fija; `ValidityReading` lleva el número de póliza y `venceEn` reales en vez de un banner de texto precalculado; `AvisoVigenciaScreen` interpola esos datos reales vía `stringResource` (2 strings nuevos, aditivos). `CustomerNavHost` ya no filtra la navegación por la póliza fija — solo por tipo de aviso; la coincidencia real de póliza se resuelve después, en el `open(push)` del dominio. `./gradlew :app:testDebugUnitTest`: BUILD SUCCESSFUL, 0 fallos.
  - **Reconciliación con #165 queda pendiente** cuando ese PR mergee — colisión esperada en `bff-movil/app/main.py`, `RemoteRepositories.kt`, `CustomerNavHost.kt`, `strings.xml` (archivos que ambos lados tocan).
- [x] **HU-60 (modificar coberturas, pendiente de WU-08)**: `apps/web/src/app/features/backoffice/polizas/` — `modificarCoberturas()` en gateway/viewmodel (mismo patrón que `renovar`/`cancelar`, reusa `POST /operador/polizas/ciclo` verbo `modificar`, ya construido en HU-59/61), formulario inline editable de coberturas (nombre/suma asegurada/deducible). Confirm-dialog no encajaba (solo soporta un motivo de texto, no una lista estructurada) — se dejó fuera deliberadamente. **2 bugs reales encontrados y corregidos**: `bff-web::_poliza_salida()` nunca exponía `coberturas` al canal web (fix de una línea, documentado como excepción al alcance declarado); un step E2E duplicado (`'the customer is signed in'`) entre `access.steps.ts` y el `self-service.steps.ts` de HU-66, bloqueando 5 escenarios ajenos — desambiguado. `modification.feature` deja de estar `@pendiente`, 45/45 escenarios E2E reales contra dev server. 441/441 Karma, 100% cobertura.
- [x] **HU-66 (autoservicio web)**: investigación confirmó que todo el comportamiento ya existía (el cliente de pólizas solo expone lectura, sin ningún método de ciclo de vida; el detalle no tiene botones de renovar/modificar/cancelar) — no faltaba construir UI, solo escribir los steps que verificaran la aserción del Gherkin (`self-service.feature`) contra el comportamiento real. `@pendiente` retirado.
- [x] **HU-67 (orquestador, acotado a avisos de vencimiento automáticos)**: `apps/backend/ms-polizas/` — `generar_avisos_vencimiento(uow, dias=30)` reusa `listar_polizas_por_vencer` (WU-07) y agrega un evento `PolizaPorVencer` al outbox por póliza en ventana, cerrando el loop `ms-polizas → outbox-relay → notificaciones` que antes solo se activaba si alguien llamaba `GET /avisos` a mano. Idempotencia vía `Outbox.existe_para_agregado(tipo, agregado_id)` (sin tocar el dominio `Poliza`). Entrypoint: script standalone `python -m app.jobs.avisos_vencimiento`, pensado para un `CronJob` de Kubernetes — el manifiesto de Helm real queda pendiente (el chart genérico no tiene ese template todavía). **Bug de test preexistente encontrado y corregido** (no introducido por este cambio, confirmado con `git stash`): `test_por_vencer_usa_30_dias_por_defecto` usaba `date.today()` (hora local) para el límite exacto de la ventana, pero `_hoy()` en producción usa `datetime.now(UTC).date()` — con la máquina en huso horario negativo y ya entrada la noche, ambas difieren un día completo y el test fallaba en el borde exacto (29/31 vs 30 días). 162/162 tests (incluye 1 de integración contra Postgres real).
- [x] **HU-68 (servicio de analítica)**: `apps/backend/analitica/` generado desde cero, mismo patrón hexagonal que `notificaciones`/`outbox-relay`. Consume `BusEventos` (mismo IAM/OAUTHBEARER), agrega un contador por (tipo, fecha) de `PolizaEmitida/Renovada/Modificada/Cancelada` y `PolizaPorVencer` (HU-67), idempotente por `evento_id` vía tabla auxiliar `evento_procesado` (sin una fila por evento individual, solo el contador agregado). `GET /v1/metricas?desde=...&hasta=...`, rol operador. `infra/k8s/values/analitica.yaml` tenía el mismo bug de `externalSecrets.habilitado: false` ya visto y corregido antes en `notificaciones.yaml` — corregido igual. 39/39 tests unitarios + 4/4 de integración verificados contra Postgres real en Docker, 79% cobertura total.
- [x] **HU-69 (dashboard de métricas, back-office)**: dos capas. `bff-web/app/routers/metricas.py` (`GET /operador/metricas`, rol operador, mismo patrón que `routers/reportes.py`) reexpone `GET /v1/metricas` de `analitica` — necesario porque ese servicio, como todos los `ms-*` internos, no está expuesto en el ALB. `apps/web/src/app/features/backoffice/metricas/` (mismo patrón que `features/backoffice/reportes/`): tabla simple de conteos, sin librería de charts (el proyecto no tiene ninguna instalada, una tabla es MVP suficiente). El back-office pasa de 5 a 6 secciones — **se actualizaron proactivamente los 5 lugares que afirmaban "cinco"/"five"** (`backoffice.layout.spec.ts`, `sections.spec.ts`, `backoffice.page.ts`, 2 `.feature` de navigation/role-permissions) para no repetir la regresión ya vista en el commit de reportes de WU-08. 157/157 bff-web (antes 152), 451/451 Karma (100% cobertura).
- [ ] WU-11 … WU-14: solo las 4 piezas de Fase 2 de siempre quedaban con ese nombre en el plan original; se reinterpretaron y cerraron como HU-66/67/68/69 arriba (el plan original agrupaba HU-66..69 bajo "Fase 2" sin desglosar WU-11..14 uno a uno) — no queda ningún WU de Fase 2 adicional sin abordar salvo lo ya documentado como pendiente abajo.

## Siguiente paso

Se retomó el 2026-11-06 tras quedarse sin créditos en opencode a mitad de WU-04. Con WU-01 a WU-10 completos y HU-60/66/67/68/69 (Fase 2) también cerradas, el recorrido completo de R6 (Fase 1 + Fase 2 del alcance original del plan) tiene implementación real en los 3 canales (back-office, cliente web, cliente móvil) más automatización de avisos y analítica/dashboard. **HU-66..69 no tienen respaldo en el enunciado oficial del curso (PDF `MISW4501-202614-Proyecto.pdf`, leído completo) ni en la wiki del proyecto** (que las agrupa como "post-MVP, sin código, ❌" sin ningún desglose) — se construyeron igual por decisión explícita del usuario ("construyámoslas igual y validamos"), con alcance definido por el equipo (yo) ante la ausencia de especificación real, anclado en el journey #6 del PDF ("gestión del ciclo de vida: renovaciones, modificaciones, cancelaciones, reportes") y en lo ya construido en WU-04 a WU-10. **Validar con el mantenedor/equipo real si el alcance que se inventó para estas 4 coincide con lo que se esperaba.**

Falta, en orden: (1) validar WU-04/WU-05 contra un MSK real (el cluster `solventa-minimo-msk` está `ACTIVE` en AWS pero vive en VPC privada, inalcanzable desde este equipo sin bastion/VPN); (2) reconciliar WU-09/WU-10 cuando el PR **#165** mergee (conflicto de merge esperado y aceptado deliberadamente, ver arriba); (3) agregar el manifiesto de Helm/K8s del `CronJob` real para el job de HU-67 (el chart genérico de `infra/k8s/charts/microservicio` no tiene ese template todavía — el script Python ya existe y es ejecutable, falta solo la pieza de infraestructura); (4) validar con el mantenedor el alcance real esperado de HU-66..69 (ver arriba).
