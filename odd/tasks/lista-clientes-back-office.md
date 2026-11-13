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
- `bff-web`: `GET /asesor/clientes` y `POST /asesor/clientes/estado` contra
  `ms-identidad` real, traduciendo al shape que el frontend ya espera.
- Tests unitarios y de API en ambos servicios.
- Este documento.

**Fuera:**

- `POST /asesor/clientes` (alta de cliente nuevo desde el back-office) SIGUE
  siendo mock -- no crea un `Usuario` real en `ms-identidad`. No fue
  necesario para HU-141 (listar/ficha/desactivar) y no se alcanzó a conectar
  en esta rama.
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

7. **`bff-web` traduce `nombre`+`apellidos` a un único campo `nombre`.** El
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
| T12 | Este documento. | `odd/tasks/lista-clientes-back-office.md` | — |

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
4. `POST /asesor/clientes` (alta) sigue siendo mock, documentado como tal en
   el código (`TODO`) y en este documento -- no se presenta como terminado.
5. `pytest -m "not integration"` en verde en `ms-identidad` (111 tests) y
   `pytest` en verde en `bff-web` (167 tests, 1 skip preexistente de
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
- [x] T12: este documento.
- Nota de entorno: al arrancar, `ms-identidad` resolvía (vía `uv.lock`)
  `starlette==1.10.0` contra `fastapi==0.162.0`, que todavía declara solo
  `starlette>=0.46.0` sin tope superior -- rompía la importación de
  `app/main.py` (`Router.__init__() got an unexpected keyword argument
  'on_startup'`) de forma intermitente según el estado del `.venv`/caché
  local. Se confirmó con `git stash` que el problema preexistía en la rama
  base (`develop`) y no lo introdujo este trabajo; se resolvió limpiando
  `.venv`/`__pycache__` y reinstalando (`uv sync`), sin cambiar ningún pin.
  Vale la pena que quien retome esto futuro valide si conviene fijar un
  tope superior a `starlette` en `ms-identidad`/`bff-web`/`bff-movil` para
  no depender de que la resolución de `uv` caiga del lado compatible.
