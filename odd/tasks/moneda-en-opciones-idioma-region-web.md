# Moneda visible en las opciones de idioma y región (web)

## Objetivo

Que el selector de idioma/región del portal (HU-108, SOLV-232 — ya en
`develop`, estado Done en Jira) deje explícito, en cada opción, qué moneda
usará ese país, sin obligar a leer solo el texto de ayuda general.

## Problema (evidencia verificada el 2026-11-13 contra el código en `develop`)

HU-108 ya está implementada y funcionando: `LocaleService`
(`apps/web/src/app/core/i18n/locale.service.ts`) persiste la elección,
`MoneyPipe`/`formatMoney` (`apps/web/src/app/core/i18n/format.ts`) ya formatea
montos con el locale activo en cliente y back-office (`svMoney` se usa en
`cotizaciones.view.html`, `asesor-cotizacion.view.html`,
`asesor-emision.view.html`, `ver-oferta.view.html`, etc.).

El único punto flojo es de claridad: la vista `idioma-region.view.html`
(`apps/web/src/app/features/idioma-region/`) muestra un `hint` general
("Elige tu región para ver moneda y fecha en el formato correcto") pero cada
botón de opción solo dice `"Español · Colombia"`, `"Español · México"`, etc.
— sin la moneda de cada país — así que no es evidente, opción por opción, qué
moneda corresponde a cada elección.

## Alcance

Dentro:

- Agregar el código de moneda ISO 4217 entre paréntesis a cada etiqueta de
  opción (`idiomaRegion.locale.es-CO/es-MX/es-CL/es-PE`) en los 4 archivos de
  traducción: `es-CO.json`, `es-MX.json`, `es-CL.json`, `es-PE.json`
  (`apps/web/src/app/core/i18n/`). Monedas usadas: COP, MXN, CLP, PEN —
  mismas que ya aparecen en `inicio.subtitle` de cada archivo.

Fuera (no se toca en esta tarea):

- Lógica de `LocaleService`, `formatMoney`/`MoneyPipe`: ya funcionan
  correctamente, no hay bug que corregir ahí.
- El `hint` general de la vista: ya menciona moneda y fecha, se deja igual.
- Paridad Android (HU-94): esta tarea es solo del canal web.

## Tareas

| ID | Tarea | Ruta | Evidencia |
| --- | --- | --- | --- |
| T1 | Añadir moneda a las 4 etiquetas de opción en los 4 locales | `apps/web/src/app/core/i18n/es-{CO,MX,CL,PE}.json` | Edición mecánica de 4 líneas por archivo; moneda confirmada contra `inicio.subtitle` del mismo archivo |

## Criterios de aceptación

- Cada opción del selector de idioma/región muestra su moneda, ej.
  `"Español · Colombia (COP)"`.
- Los 4 archivos JSON siguen siendo válidos (`json.load` sin error).
- Los tests existentes de `idioma-region.view.spec.ts` siguen en verde (usan
  `getByTestId`, no texto exacto, así que no deberían romperse).
- Los `e2e` de `idioma-region`/`language-region` siguen en verde (usan
  `getByTestId` vía `idioma-region.page.ts`, no el texto visible).
