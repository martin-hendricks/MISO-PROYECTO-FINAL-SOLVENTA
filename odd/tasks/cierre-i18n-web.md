# Cierre de la internacionalización del canal web (HU-108)

## Objetivo

Cerrar los huecos que quedaron en la internacionalización del portal
(HU-108, SOLV-232) frente a su criterio de aceptación, manteniendo el alcance
acordado con el equipo: solo español, cuatro locales (`es-CO`, `es-MX`,
`es-CL`, `es-PE`), formato en el canal (PL-01), sin traducir el núcleo ni
convertir divisas.

## Problema (evidencia verificada el 2026-11-20 contra `develop`)

La base ya estaba: `ngx-translate` con 4 catálogos, `LocaleService`
persistente, pipes `svMoney`/`svDate`/`svDateTime`, selector en primer
arranque y en Perfil, y ninguna cadena fija en plantillas. Faltaba:

1. **Formato de moneda fuera del criterio.** El Gherkin de HU-108 exige
   `$1,234.56 MXN`; `formatMoney` usaba `maximumFractionDigits: 0` y daba
   `$1,235 MXN`. Por eso `customer-portal/language-region.feature` seguía
   `@pendiente`.
2. **Claves faltantes.** `cotizacion.campo.descripcion.*` (7 claves) solo
   existía en `es-CO`; MX/CL/PE caían al fallback sin ningún error visible.
3. **`<html lang>` fijo** en `es-CO` (`index.html`) aunque el usuario
   cambiara de locale: lectores de pantalla pronunciaban con el locale
   equivocado.
4. **Sin ejemplo visible** de prima y fecha en el selector, que es lo que el
   escenario "Locale México formatea en el canal" verifica.

Descartado tras revisión: los `Error('Sin sesión')`, `'Token ilegible'` y
`'Consentimiento sin registrar'` nunca se muestran al usuario (nadie lee
`.message`), así que no requieren traducción.

## Alcance

Dentro:

- `formatMoney`: centavos solo cuando el monto los tiene
  (`trailingZeroDisplay: 'stripIfInteger'`), con decimales fijados por
  moneda (COP y CLP 0, MXN y PEN 2, resto 2). Se fijan en código porque el
  ICU de cada motor difiere (Chrome 157 trata COP con 0 decimales, Node 22
  con 2).
- Las 7 claves faltantes en `es-MX/CL/PE.json` y una prueba de paridad que
  obliga a los 4 catálogos a tener exactamente las mismas claves.
- `LocaleService` sincroniza `document.documentElement.lang` al arrancar
  (vía `provideAppInitializer`) y en cada cambio.
- Vista previa en `idioma-region` (ruta y diálogo de Perfil): prima de
  ejemplo `1234.56` en la moneda del locale y fecha `2026-07-09`.
- `language-region.feature` deja de ser `@pendiente`, con sus pasos.

Fuera:

- Idiomas distintos del español, traducción del núcleo, conversión de
  divisa (sin cambios de alcance en HU-108).
- Resto de HU-106 / SOLV-230 (diálogos de consentimiento y logout en
  Perfil).
- Paridad Android (HU-94).

## Tareas

| ID | Tarea | Ruta | Evidencia |
| --- | --- | --- | --- |
| T1 | Centavos condicionales y decimales por moneda | `apps/web/src/app/core/i18n/format.ts` | `format.spec.ts` (MXN `$1,234.56`, COP `$ 42.300`, CLP redondea, PEN `S/ 1,234.50`) |
| T2 | Claves faltantes + paridad de catálogos | `apps/web/src/app/core/i18n/es-{MX,CL,PE}.json` | `catalogs.parity.spec.ts` |
| T3 | `<html lang>` sigue al locale | `locale.service.ts`, `app.config.ts` | `locale.service.spec.ts` |
| T4 | Vista previa en el selector + e2e activo | `features/idioma-region/*`, `e2e/steps/idioma-region.steps.ts`, `e2e/features/customer-portal/language-region.feature` | `idioma-region.view.spec.ts`, Cucumber |

## Criterios de aceptación

- Con Español · México, la vista previa muestra `$1,234.56 MXN` y
  `09/07/2026` (Gherkin de HU-108).
- Montos enteros siguen sin decimales en todas las vistas (`svMoney`).
- Los 4 catálogos tienen las mismas claves.
- `<html lang>` coincide con el locale activo.
- `ng test` en verde con cobertura 100 %; e2e `@HU-108` en verde.
