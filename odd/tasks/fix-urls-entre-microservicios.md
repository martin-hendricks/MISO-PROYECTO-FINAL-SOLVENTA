# fix-urls-entre-microservicios

## Objetivo

Eliminar los 503 que produce bff-web en `POST /v1/cliente/polizas` y
`POST /v1/asesor/emisiones/{id}/poliza` corrigiendo las URLs internas entre
microservicios que están sin definir o sin puerto en los values de Kubernetes.

## Problema

`POST /v1/cliente/polizas` devuelve 503 con
`{"codigo":"servicio_no_disponible","mensaje":"Intenta de nuevo en unos minutos"}`
(80 bytes). bff-web registra `servicio no disponible: ms-cotizacion`, pero
ms-cotizacion nunca devuelve 5xx: devuelve
`503 {"codigo":"dependencia_no_disponible","mensaje":"ms-suscripcion no está disponible"}`.

## Por qué

`ms-cotizacion` no tiene definida `MS_SUSCRIPCION_URL` en su values, así que
cae al default de `app/config.py`: `http://ms-suscripcion:8000`. El Service
`ms-suscripcion` escucha en **8080**. El puerto 8000 no tiene regla DNAT, así
que el paquete se descarta y `httpx` espera hasta agotar
`timeout_dependencias = 2.0 s` → `DependenciaNoDisponible` → 503.

Medido en el cluster: `http://ms-suscripcion:8000` → ConnectTimeout 5234 ms;
`http://ms-suscripcion:8080` → 201 en 40 ms.

bff-web además traduce cualquier status ≥400 no tipificado (incluido ese 503)
a su propio 503, lo que oculta la causa real.

## Alcance

Solo configuración de despliegue (`infra/k8s/values`) más el default de
ms-cotizacion que quedó mal escrito. No cambia contratos ni lógica de negocio.

Servicios con el mismo defecto, verificados contra el cluster:

| Servicio | Variable | Situación |
|---|---|---|
| ms-cotizacion | `MS_SUSCRIPCION_URL` | no definida → default `:8000` (puerto equivocado) |
| ms-pagos | `MS_SUSCRIPCION_URL` | no definida → default `localhost:8081` (ConnectError) |
| ms-polizas | `MS_SUSCRIPCION_URL`, `MS_PAGOS_URL` | no definidas → `localhost:8081`/`:8082` (ConnectError) |
| api-socios | `MS_IDENTIDAD_URL` | definida **sin puerto** → ConnectTimeout 3125 ms |
| ms-suscripcion | `MS_POLIZAS_URL`, `MS_IDENTIDAD_URL` | definidas **sin puerto** → URLError 3059 ms |

## Tareas

- [x] 1. ms-cotizacion: definir `MS_SUSCRIPCION_URL` en values y corregir el default de `app/config.py` y su README
- [x] 2. ms-pagos: definir `MS_SUSCRIPCION_URL` en values
- [x] 3. ms-polizas: definir `MS_SUSCRIPCION_URL` y `MS_PAGOS_URL` en values
- [x] 4. api-socios: agregar `:8080` a `MS_IDENTIDAD_URL`
- [x] 5. ms-suscripcion: agregar `:8080` a `MS_POLIZAS_URL` y `MS_IDENTIDAD_URL`
- [x] 6. Verificar con `helm template` que cada values renderiza URLs completas
- [x] 7. Commit del work unit
- [x] 8. ms-consentimiento: agregar `:8080` a `MS_IDENTIDAD_URL` (hallado por el verificador independiente)
- [x] 9. Documentar los defaults de ms-pagos/ms-polizas como solo-locales

## Criterios de aceptación

- Cada `helm template charts/microservicio -f values/<svc>.yaml` renderiza la(s)
  URL(s) afectada(s) como FQDN con puerto explícito.
- Ningún value define un puerto distinto al que expone el Service destino.
- Tras desplegar, `POST /v1/cotizaciones/{id}/aceptacion` deja de agotar 2 s
  contra `ms-suscripcion:8000`.

## Verificación

- `helm template` por servicio (render de las variables de entorno).
- Comparación puerto en values contra `kubectl get svc`.

## Progreso

- Rama: `feature/fix-urls-entre-microservicios` (desde `origin/develop` 1d821b0).
- Diagnóstico en vivo completado contra el cluster `solventa-minimo-eks`.
- Skill registry: no disponible en Engram (store vacío) → sin estándares
  específicos inyectados.
- TDD: no aplica (solo configuración YAML y un default de settings).

## Verificación ejecutada

- `helm template <svc> charts/microservicio -f values/<svc>.yaml` para los 14
  values: **todos renderizan**. Las variables afectadas salen como FQDN con
  puerto explícito.
- `grep` de `svc.cluster.local"` sobre `values/`: **ninguna URL sin puerto**.
- `Settings().ms_suscripcion_url` (venv de ms-cotizacion): `http://ms-suscripcion:8080`.
- Verificador independiente (contexto limpio) sobre `5f39e34`: confirmó las 6
  correcciones declaradas, el mapeo 503 de bff-web y el flujo de asesor; refutó
  la afirmación de "clase cerrada" por `ms-consentimiento` (corregido en
  `6116b05`).
- `gentle-ai review assess`: `risk: high`, `review_due: true`. El review nativo
  no corre en este runtime (`immutable_review_transport_unsupported`), así que
  la verificación fue writer + verificador independiente.

## Commits

- `5f39e34` — fix(infra): define las URLs internas entre microservicios con puerto explícito
- `6116b05` — fix(infra): cierra el último MS_*_URL sin puerto y documenta los defaults locales

## Siguiente paso

Desplegar los values corregidos (helm upgrade de ms-cotizacion, ms-pagos,
ms-polizas, api-socios, ms-suscripcion, ms-consentimiento) y verificar que
`POST /v1/cotizaciones/{id}/aceptacion` deja de agotar los 2 s contra
`ms-suscripcion:8000`.
