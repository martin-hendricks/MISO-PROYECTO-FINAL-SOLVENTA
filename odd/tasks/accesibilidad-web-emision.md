# Accesibilidad web: pantalla de emisión del cliente

## Objetivo

Cerrar el único foco de violaciones de axe que quedó en `develop` tras
`accesibilidad-web-prestadores-socios`: la pantalla `/emision`, y que el e2e normal la vigile.

## Problema (comparación main vs develop del 2026-11-21)

`/emision` vive fuera del shell del portal, así que no hereda su `<main>`:

| Regla de axe | Causa en `emision.view.html` |
| --- | --- |
| `landmark-one-main` (3 escenarios) | La vista no tiene `<main>`. |
| `region` (2 escenarios) | El contenido queda fuera de cualquier landmark. |
| `page-has-heading-one` (1 escenario) | Los estados expirada, revocada y error no tienen ningún encabezado; el de enlace inválido usa `<h2>`. Emitida y en progreso ya tenían `<h1>`. |

## Alcance

Dentro: `apps/web/src/app/features/emision/`, las 4 traducciones `core/i18n/es-{CO,MX,CL,PE}.json`
y tres `.feature` de e2e.

Fuera: contraste, el resto de la pantalla, el flujo de emisión en sí.

## Tareas

| ID | Tarea |
| --- | --- |
| T1 | Envolver la vista en `<main>`; la barra superior queda fuera, como banner. |
| T2 | `<h1>` en los estados expirada, revocada y error (claves `emision.{expired,revoked,error}.title`) y cambiar el `<h2>` del enlace inválido a `<h1>`. |
| T3 | Step de axe en los 3 escenarios que terminan en `/emision`: `home`, `navigation` y `revoked-consent`. |

## Criterios de aceptación

- [x] Test Karma por cada fila de Problema (`main` único, un `<h1>` en cada estado).
- [x] `pnpm test`: 680/680, cobertura 100%.
- [x] `pnpm build` sin errores.
- [x] Los 3 escenarios con axe en verde contra el build de producción.
- [x] Sin regresiones: `@customer-portal`, `@subscription` y `@quotation`, 25 de 25.

## Limitaciones

- Los títulos nuevos (`Oferta vencida`, `Autorización revocada`, `No pudimos emitir tu póliza`)
  son copy propuesto por ingeniería; conviene que producto los revise.
- No se corrió la suite e2e completa.
