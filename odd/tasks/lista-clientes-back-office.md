# lista-clientes-back-office (HU-141)

> Rama: `feature/HU-141-lista-clientes` · Base: `develop` (`c9ab895`, 2026-11-12)

## Objetivo

Que el back-office (asesor/operador) pueda consultar la lista real de
clientes, ver la ficha de uno individual y activar/desactivar su cuenta,
contra `ms-identidad` real a través de `bff-web` -- sin tocar el contrato
HTTP que el frontend ya consume.

## Problema

`apps/backend/bff-web/app/routers/asesor.py` tenía `GET /clientes`, `POST
/clientes` y `POST /clientes/estado` respondiendo contra una lista
hardcodeada en memoria (`CLIENTES`, 5 clientes fijos), cada uno con un
comentario explícito:

```python
# TODO: el CRM de clientes depende de ms-identidad (no existe código, solo
# README en cualquier rama) -- no hay microservicio real al que integrar.
@router.get("/clientes")
def listar() -> dict:
    return {"clientes": [dict(cliente) for cliente in CLIENTES]}
```

`ms-identidad` ya tiene arquitectura hexagonal completa para `Usuario` (con
`rol` enum cliente/asesor/operador), pero ningún caso de uso ni endpoint
para listar/consultar/desactivar usuarios con `rol="cliente"` pensado para
el back-office -- solo `consultar_usuario`/`actualizar_perfil` (uso propio
del cliente) y `buscar_por_documento` (resuelve un `usuario_id`, nada más).

El frontend (`apps/web/src/app/features/backoffice/clientes/`) ya está
construido contra el contrato que `bff-web` expone (`GET
{baseUrl}/asesor/clientes` -> `{clientes: Cliente[]}`), consumiendo el mismo
mock -- la UI funciona hoy, pero sobre datos de mentira.

## Alcance

**Dentro:**

- `ms-identidad`: casos de uso y endpoints de listar/ficha/desactivar
  clientes para el back-office; columna `canal` en `usuario`; resolución del
  campo `consentimiento` combinando `ms-consentimiento` (habeas data) y
  `ms-perfilamiento` (consentimiento de perfilamiento hipotecario +
  originación abierta).
- `bff-web`: `GET /asesor/clientes`, `POST /asesor/clientes` (alta real) y
  `POST /asesor/clientes/estado` contra `ms-identidad` real, traduciendo al
  shape que el frontend ya espera.
- Tests unitarios y de API en ambos servicios.
- Este documento.

**Fuera:**

- Cualquier implementación de `ms-consentimiento`: ese servicio lo construye
  otro equipo en paralelo (otra rama/worktree), contra un contrato ya
  coordinado. Este trabajo solo configura la URL esperada
  (`MS_CONSENTIMIENTO_URL`, default `http://ms-consentimiento:8080`) y
  construye el cliente HTTP contra ese contrato -- no se puede probar contra
  el servicio real todavía porque no existe en este árbol.
- Propagación de eventos de dominio desde `ms-consentimiento` (fuera de
  alcance de este flujo: aquí solo se *consulta* ese servicio, nunca se
  reacciona a sus eventos).
- Rediseño de UI: las pantallas de Figma `lista-clientes`/`detalle-cliente`
  no se tocaron -- el frontend ya existía y consumía el contrato correcto
  (confirmado leyendo `clientes.gateway.ts`), así que no hubo cambios de UI.
- `canal` no se popula todavía desde ningún flujo de registro real (web o
  android): la columna queda nullable a propósito, usuarios existentes y
  nuevos siguen sin ese dato hasta que exista una HU que lo pida en el alta.
- Paginación del listado de clientes (hoy sin volumen que la justifique).

## Decisiones de diseño

1. **"Cliente" = `Usuario` con `rol="cliente"`.** No se creó una entidad de
   dominio nueva: los casos de uso nuevos (`app/application/
   casos_uso_clientes.py`) operan sobre el mismo agregado `Usuario`, con un
   candado explícito (`usuario.rol != "cliente"` -> `NoEncontrado`) para que
   el back-office no "fiche" ni desactive asesores/operadores por esta vía.

2. **Resolución de `consentimiento` (3 reglas, en este orden de
   prioridad):**
   1. `ms-perfilamiento` tiene una `Originacion` con `cerrada_en IS NULL`
      (abierta) para ese cliente -> `"hipotecario_pendiente"`.
   2. Si no, y `ms-consentimiento` confirma habeas data vigente (200,
      `vigente=true`) -> `"habeas_data"`.
   3. Cualquier otro caso -> `"revocado"`.

   Una originación hipotecaria abierta importa más que el estado del habeas
   data para el back-office: se prioriza mostrar que hay un crédito en
   trámite.

3. **Ambigüedad del 404 de `ms-consentimiento` (documentada, no resuelta
   contra el servicio real porque no existe aún):** el contrato acordado es
   `GET /v1/consentimientos/{cliente_id}` -> 200 `{"vigente": true, ...}` si
   hay consentimiento vigente, o 404 si nunca se otorgó **o** si fue
   otorgado y luego revocado -- el contrato no distingue esos dos casos en
   el 404. `ClienteConsentimientoHTTP.vigente()`
   (`app/infrastructure/consentimiento_http.py`) trata ambos casos igual:
   devuelve `False` sin distinguir "nunca otorgado" de "revocado", porque el
   campo de salida `consentimiento` tampoco distingue esos dos orígenes (en
   cualquiera de los dos casos cae en `"revocado"` por la regla 3 de
   arriba). Queda documentado en el docstring del puerto
   (`app/ports/consentimiento.py`) para quien integre contra el servicio
   real y quiera revisar si el contrato cambia.

4. **Degradación ante caída de un servicio externo.** Ninguna de las dos
   llamadas (`ms-consentimiento`, `ms-perfilamiento`) puede tumbar el
   listado completo de clientes por un error de un campo secundario. Ambos
   adaptadores HTTP (`consentimiento_http.py`, `perfilamiento_http.py`)
   capturan `httpx.HTTPError` y cualquier `status_code >= 400` no 404,
   registran una advertencia en el log (`logger.warning`, no `error`: es un
   comportamiento esperado mientras `ms-consentimiento` no esté desplegado)
   y devuelven `False` -- lo que la regla de combinación traduce a
   `"revocado"` para ese cliente, sin afectar al resto del listado.

5. **Shape de salida con `estado`/`consentimiento` en minúsculas.**
   `ClienteSalida.desde()` (`app/api/v1/schemas_clientes.py`) convierte
   `EstadoUsuario.ACTIVO`/`INACTIVO` a `"activo"`/`"inactivo"` dentro de
   `ms-identidad`: así ni `bff-web` ni el frontend tienen que traducir el
   enum en mayúsculas que usa el resto del servicio.

6. **Guard de rol nuevo (`exigir_rol_backoffice`).** Mismo patrón que
   `exigir_busqueda_por_documento` (`app/seguridad.py`): los 3 endpoints
   nuevos de `ms-identidad` (`GET /v1/clientes`, `GET /v1/clientes/
   {usuario_id}`, `PATCH /v1/clientes/{usuario_id}/estado`) solo aceptan rol
   `asesor`/`operador` -- ni el propio cliente ni un `socio` externo pueden
   listar la cartera completa.

8. **Alta real de cliente desde el back-office (`POST /asesor/clientes`).**
   Ya no es mock: crea un `Usuario` real en `ms-identidad`
   (`POST /v1/usuarios`, mismo endpoint que usa el alta del propio cliente
   en `registro.py`) y, si el asesor marcó `habeasData`, otorga el
   consentimiento real en `ms-consentimiento`
   (`ClienteMsConsentimiento.otorgar_consentimiento`) -- a diferencia de
   `registro.py`, que todavía lo simula (ver su comentario "Stub hasta que
   ms-consentimiento versione la política"). Tres decisiones puntuales:
   - **Contraseña temporal.** El formulario de alta del back-office no
     captura una contraseña del cliente (la define el propio cliente, no el
     asesor): se genera una aleatoria con `secrets.token_urlsafe(18)`. No
     existe todavía ningún flujo de "cambiar contraseña" ni de notificación
     por correo en el proyecto, así que esa contraseña no llega a ningún
     lado hoy -- deuda explícita, no resuelta en esta rama.
   - **Separación de nombre/apellidos.** `ms-identidad` los guarda por
     separado; el formulario solo captura un nombre completo. Se toma la
     primera palabra como nombre y el resto como apellidos
     (`_separar_nombre()` en `asesor.py`).
   - **`canal` fijo en `"web"`.** El alta desde el back-office ocurre en el
     canal web del asesor; `ClienteNuevo.canal` queda como campo del body
     por si a futuro el back-office atiende otro canal, pero hoy siempre se
     envía `"web"` desde el formulario actual del frontend.
   - Si `ms-consentimiento` no responde al otorgar, la petición completa
     devuelve 503 (no se degrada a 201 silencioso): el `Usuario` ya quedó
     creado en `ms-identidad`, pero es más honesto fallar visiblemente que
     responder éxito sobre un consentimiento que en realidad no se otorgó.

9. **`bff-web` traduce `nombre`+`apellidos` a un único campo `nombre`.** El
   frontend (`clientes.gateway.ts`/`clientes.testing.ts`) espera el nombre
   completo en un solo string (p.ej. `"Andrés Gómez"`), mientras
   `ms-identidad` los guarda por separado -- `_cliente_desde_identidad()` en
   `asesor.py` los concatena. También aplana `documento` (objeto
   `{tipo, numero}` en `ms-identidad`) al único string que el frontend
   espera.

## Tareas

| ID | Tarea | Ruta | Evidencia |
| --- | --- | --- | --- |
| T1 | Migración `canal TEXT` nullable en `usuario`, con CHECK `web`/`android`. | `apps/backend/ms-identidad/db/05_canal_usuario.sql` | Sigue el patrón de `04_rol_usuario.sql`. |
| T2 | Campo `canal` en el dominio `Usuario` + mapeo SQL (`UsuarioFila`, `_fila`/`_a_dominio`). | `app/domain/modelos.py`, `app/infrastructure/sql.py` | Tests en `tests/test_infraestructura.py`. |
| T3 | `RepositorioUsuarios.listar_por_rol` (puerto + SQL + doble en memoria). | `app/ports/persistencia.py`, `app/infrastructure/sql.py`, `tests/dobles.py` | `test_listar_por_rol_*` en `tests/test_infraestructura.py`. |
| T4 | Puertos `ConsultaConsentimiento`/`ConsultaPerfilamiento` + adaptadores HTTP con degradación. | `app/ports/consentimiento.py`, `app/ports/perfilamiento.py`, `app/infrastructure/consentimiento_http.py`, `app/infrastructure/perfilamiento_http.py` | `tests/test_clientes_http.py` (11 tests: vigente, 404, 5xx, timeout/ConnectError, JSON inválido). |
| T5 | Config: `MS_CONSENTIMIENTO_URL`, `MS_PERFILAMIENTO_URL`, timeout dedicado. | `app/config.py` | — |
| T6 | Casos de uso `listar_clientes`/`obtener_cliente`/`actualizar_estado_cliente`/`resolver_consentimiento`. | `app/application/casos_uso_clientes.py` | `tests/test_casos_uso_clientes.py` (15 tests). |
| T7 | Guard `exigir_rol_backoffice`. | `app/seguridad.py` | Cubierto en `tests/test_api_clientes.py` (403 para cliente/socio). |
| T8 | Endpoints `GET /v1/clientes`, `GET /v1/clientes/{usuario_id}`, `PATCH /v1/clientes/{usuario_id}/estado`. | `app/api/v1/rutas_clientes.py`, `app/api/v1/schemas_clientes.py`, registrados en `app/main.py` | `tests/test_api_clientes.py` (17 tests). |
| T9 | `ClienteMsIdentidad.listar_clientes`/`actualizar_estado_cliente` (bff-web). | `apps/backend/bff-web/app/clients/ms_identidad.py` | Cubierto vía `tests/test_asesor.py`. |
| T10 | `GET /asesor/clientes` y `POST /asesor/clientes/estado` reales (ya no mock), traductor `_cliente_desde_identidad`. | `apps/backend/bff-web/app/routers/asesor.py` | `tests/test_asesor.py`: listado, 503 si cae ms-identidad, 404 si no existe, nombre completo, documento aplanado. |
| T11 | Fix de tests existentes que dependían del mock (`test_cartera_ficha_y_venta`, `test_listado_de_clientes_trae_canal_y_consentimiento`, `test_sin_rol_el_bff_asigna_asesor`). | `apps/backend/bff-web/tests/test_asesor.py`, `tests/test_sesion.py` | Ya no asumen 200 "gratis"; registran la respuesta esperada de `ms-identidad` vía `nucleo_identidad`. |
| T12 | `canal` opcional en el schema de alta de `ms-identidad` (`CrearUsuarioEntrada`/`UsuarioSalida`), pasado a `casos_uso.crear_usuario` (el dominio ya lo aceptaba). | `app/api/v1/schemas.py`, `app/api/v1/rutas.py`, `app/application/casos_uso.py` | `test_alta_con_canal_lo_persiste`, `test_alta_sin_canal_queda_nulo` (`tests/test_api.py`), `test_crear_usuario_con_canal_lo_persiste` (`tests/test_casos_uso.py`). |
| T13 | Alta real de cliente desde el back-office: `POST /asesor/clientes` crea el `Usuario` en `ms-identidad` y otorga el consentimiento en `ms-consentimiento` (ya no el mock `CLIENTES`). Cliente HTTP nuevo `ClienteMsConsentimiento`. | `apps/backend/bff-web/app/routers/asesor.py`, `app/clients/ms_consentimiento.py`, `app/clients/ms_identidad.py`, `app/dependencies.py`, `app/main.py`, `app/config.py` | `tests/test_asesor.py`: alta feliz, sin habeasData (422), documento duplicado (409), rechazo KYC (422), caída de ms-consentimiento (503), separación de nombre/apellidos (1 y 2+ palabras). 100% cobertura en `asesor.py`/`ms_consentimiento.py`/`ms_identidad.py`. |
| T14 | Este documento. | `odd/tasks/lista-clientes-back-office.md` | — |

## Criterios de aceptación

1. `ms-identidad`: `GET /v1/clientes` devuelve solo usuarios con
   `rol="cliente"`, con `clienteId/nombre/apellidos/documento/canal/estado/
   consentimiento`; `GET /v1/clientes/{usuario_id}` devuelve la misma ficha
   para un cliente puntual y 404 si no existe o no es cliente; `PATCH
   /v1/clientes/{usuario_id}/estado` activa/desactiva y devuelve el cliente
   actualizado. Los 3 solo aceptan rol `asesor`/`operador` (403 en cualquier
   otro rol, 401 sin token).
2. El campo `consentimiento` se resuelve con la regla de 3 niveles descrita
   arriba, y una caída de `ms-consentimiento` o `ms-perfilamiento` nunca
   produce un 5xx en el listado completo -- solo degrada ese campo a
   `"revocado"` para el cliente afectado.
3. `bff-web`: `GET /asesor/clientes` y `POST /asesor/clientes/estado` hablan
   con `ms-identidad` real; el shape de salida coincide exactamente con lo
   que `apps/web/.../clientes.gateway.ts` ya espera (sin cambios en el
   frontend).
4. `POST /asesor/clientes` (alta) crea un `Usuario` real en `ms-identidad`
   (ya no mock) y, si el asesor marca `habeasData`, otorga el consentimiento
   real en `ms-consentimiento`; responde 422 sin `habeasData`, 409 si el
   documento/correo ya existe, 503 si `ms-consentimiento` no responde al
   otorgar (el alta en `ms-identidad` ya quedó hecha, pero la respuesta
   completa no se presenta como éxito sobre un consentimiento que no se
   otorgó).
5. `pytest -m "not integration"` en verde en `ms-identidad` (116 tests) y
   `pytest` en verde en `bff-web` (173 tests, 1 skip preexistente de
   contrato).

## Verificación

```bash
cd apps/backend/ms-identidad && uv run pytest -m "not integration" -q
cd apps/backend/bff-web && uv run pytest -q
```

## Progreso

- [x] T1-T8 (`ms-identidad`): migración, dominio, repositorio, puertos y
  adaptadores HTTP de consentimiento/perfilamiento con degradación,
  casos de uso, guard de rol, endpoints y schemas. 111/111 tests
  (`pytest -m "not integration"`), 98% cobertura total, 100% en todo el
  código nuevo (`casos_uso_clientes.py`, `rutas_clientes.py`,
  `schemas_clientes.py`, `consentimiento_http.py`, `perfilamiento_http.py`,
  `ports/consentimiento.py`, `ports/perfilamiento.py`).
- [x] T9-T11 (`bff-web`): cliente HTTP extendido, endpoints reales,
  traductor de shape, fix de 3 tests que dependían del mock anterior.
  167/167 tests (1 skip preexistente de contrato, sin relación con este
  cambio), 100% cobertura en `asesor.py` y `ms_identidad.py`.
- [x] T12-T13: alta real de cliente conectada (ya no mock) + `canal`
  opcional en el alta de `ms-identidad`. 116/116 tests en `ms-identidad`
  (98% cobertura total), 173/173 en `bff-web` (1 skip preexistente de
  contrato, 100% cobertura en los 3 archivos tocados).
- [x] T14: este documento.
- Nota de entorno (investigada aparte, confirmada no bloqueante): se
  reprodujo el escenario reportado con `fastapi==0.162.0` +
  `starlette==1.10.0` instalando en un venv **completamente limpio** (no
  `uv`, `pip install -c requirements.lock ".[test]"` desde cero) tanto en
  esta rama como en `develop` sin ningún cambio -- los 113/116 tests pasan
  en ambos casos. No se reproduce la falla de `Router.__init__()` que
  reportó el intento anterior: fue un problema puntual de caché/entorno
  local de esa sesión, no una incompatibilidad real entre esas versiones.
  No se tocó ningún pin.
