# Accesibilidad web: completar lo nuevo (billetera, notificaciones, perfil, clientes, shell)

## Objetivo

Cerrar los huecos de accesibilidad de `apps/web/` en las vistas agregadas después del plan
`feature/accesibilidad-web` (commit `b1da466`, ya en `develop`), y cubrirlas con el chequeo
de axe que ese plan dejó montado.

## Línea base (ya hecho en `b1da466`, no se toca)

- `confirm-dialog`: `aria-labelledby`/`aria-describedby`, `cdkTrapFocus`, Escape, y devolución
  de foco en `avisos` y `poliza-backoffice-detalle` (`core/a11y/focus-restore.ts`).
- Patrón canónico de formularios: `aria-invalid` + `aria-describedby` con `id` por campo.
- `e2e/support/a11y.ts` + step `the current page has no accessibility violations`
  (`color-contrast` fuera de alcance: es auditoría de diseño).
- Axe conectado solo a login, registro, cotizar, cancelación y firma de asesor.

## Problema (auditado el 2026-11-19 contra `develop`)

Lo nuevo no usa nada de esa base:

| Vista | Hueco |
| --- | --- |
| `shell.layout` | Sin enlace "saltar al contenido". Overlay del menú móvil sin trampa de foco, sin Escape y sin `aria-controls`. Avatar con solo `title`. |
| `backoffice/notificaciones` | Contadores de caracteres sin vínculo al campo (`aria-describedby`). Campos obligatorios sin `aria-required`. El resultado del envío es `role="status"` con tres números sueltos, sin etiqueta. `<aside>` sin nombre. |
| `billetera-detalle` | `<h1>` solo en el estado con datos: en carga, error y "no encontrado" la página no tiene encabezado de nivel 1. |
| `perfil/consentimiento-perfil` | Usa `confirm-dialog` sin devolver el foco al botón que lo abrió al cancelar. |
| `backoffice/clientes` | Igual que perfil con el diálogo de desactivar. Formulario sin `aria-required`, correo sin `type="email"` ni `autocomplete`. Paginación sin `<nav>` con nombre. |
| e2e | Ningún escenario de billetera, notificaciones, consentimiento de perfil ni clientes ejecuta axe. |

Fuera de esos casos, billetera lista/detalle, notificaciones y clientes ya cumplen: tablas
con `<caption>` y `th scope`, `role="alert"`/`status` en error y carga, `fieldset`/`legend`
en la audiencia, `aria-haspopup="dialog"` en perfil.

## Alcance

Dentro: `apps/web/src/app/features/{shell,backoffice/notificaciones,backoffice/clientes,billetera/detalle,perfil}`,
las 4 traducciones `core/i18n/es-{CO,MX,CL,PE}.json`, specs Karma de lo tocado y los
`.feature` de e2e listados abajo.

Fuera: contraste de color, `prefers-reduced-motion`/`prefers-contrast` (diseño), linter de
Angular, paridad Android.

## Tareas

| ID | Tarea |
| --- | --- |
| T1 | Shell: skip link a `<main id="contenido-principal">`, `aria-controls` en el botón del menú, `cdkTrapFocus` + Escape en el overlay, avatar con rol/nombre. |
| T2 | Notificaciones: `aria-describedby` en título y mensaje hacia su contador, `aria-required`, resultado con etiquetas visibles, `aria-labelledby` en la vista previa. |
| T3 | Billetera detalle: `<h1>` presente en todos los estados. |
| T4 | Devolver el foco tras cancelar el diálogo en `consentimiento-perfil` y `clientes`. |
| T5 | Clientes: `aria-required`, correo con `type="email"`/`autocomplete`, paginación en `<nav>` con nombre. |
| T6 | E2E: step de axe en billetera, notificaciones, consentimiento de perfil y clientes. |

## Criterios de aceptación

- [x] Cada fila de la tabla de Problema queda cerrada con un test Karma que fija el atributo.
- [x] `pnpm test` en verde: 540/540, cobertura 100% (4 ejes).
- [x] `pnpm build` sin errores.
- [ ] `pnpm e2e` con los escenarios nuevos de axe en verde contra el stack completo
      (pendiente de correr: necesita `bff-web` en `:8080`, igual que el plan anterior).

## Progreso

- [x] T1 a T5 implementadas con tests Karma.
- [x] T6: step de axe agregado a 6 escenarios (billetera x2, notificaciones x2, consentimiento
      de perfil, clientes). Sin ejecutar.
- [ ] Correr `pnpm e2e` contra el stack completo, tanto los escenarios de este plan como los 5
      del plan anterior (`b1da466`), y corregir lo que axe reporte.
