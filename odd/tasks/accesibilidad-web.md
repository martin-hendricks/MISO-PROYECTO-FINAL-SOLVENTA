# Accesibilidad — apps/web

> Fecha: 2026-11-07. Disparador: revisión de un proyecto de referencia externo
> (`MISW4104_202512_E04`, otro curso, Angular) para evaluar qué técnicas de
> accesibilidad usar en `apps/web/` de Solventa.

## Contexto y por qué

Se investigaron dos cosas antes de este plan:

1. **El proyecto de referencia** (`/Users/juancamilo/Universidad/web/MISW4104_202512_E04/`)
   resultó tener accesibilidad **mínima y parcial, no un sistema implementado**: algunos
   patrones puntuales correctos (botones reales en vez de `<div click>`, `alt` descriptivo,
   `label for`/`id` asociados, `aria-expanded` en botones "mostrar más") mezclados con huecos
   grandes y consistentes — formularios sin `aria-describedby`/`aria-invalid`/`role="alert"`,
   un modal sin `role="dialog"` ni manejo de foco, cero `@angular/cdk/a11y`, cero testing
   automatizado de accesibilidad, cero documentación. **No hay nada que "copiar como sistema"**
   de ese proyecto.

2. **El estado real de `apps/web/` (Solventa)**, auditado en detalle: contra lo esperado, **ya
   tiene una base de accesibilidad considerablemente más madura que el proyecto de referencia**
   — no es un vacío, es un sistema parcial bien aplicado en la mayoría de los casos (20/34
   vistas con algún `aria-`), con huecos concretos y acotados, no genéricos.

Por eso este plan **no construye accesibilidad desde cero**: extiende lo que ya existe,
cierra 5 huecos puntuales ya identificados, y agrega la infraestructura de verificación que
falta (testing automatizado, utilidades compartidas de foco).

## Qué ya está bien (no tocar, es la base a mantener)

Confirmado con archivo+línea en la auditoría — documentado aquí solo como referencia de
convención a seguir en las tareas nuevas, **no se re-explica en cada tarea**:

- `aria-invalid` + `aria-describedby` con `id` único por campo, patrón repetido en
  `login`, `registro`, `consentimiento`, `riesgo-fields`, `vida-crediticia` (ej.
  `registro.view.html:25-26`). **Este es el patrón canónico a replicar** en los formularios
  que no lo tienen todavía.
- `role="alert"`/`role="status"` consistentes para mensajes de error vs. de estado.
- `aria-hidden="true"` en iconografía decorativa, aplicado sistemáticamente.
- Cero `<div>`/`<span>` clickeables no semánticos — todo pasa por `<button>` real.
- `role="radiogroup"` + `aria-checked`/`aria-labelledby` en selección de idioma/región y
  campos de riesgo.
- `<nav aria-label>` real en shell y back-office, 9 vistas con `<main>`/`<header>` semánticos.
- Labels accesibles traducidos vía `| translate` (`@ngx-translate/core`) — patrón correcto
  para este stack, no usar `i18n-*` nativo de Angular (el proyecto no lo usa en ningún lado).

## Alcance: 5 huecos concretos + infraestructura

### 1. `confirm-dialog` — el modal reutilizable (alto impacto, 2 consumidores reales)

`apps/web/src/app/features/backoffice/confirm-dialog/`: hoy tiene `role="alertdialog"` y
`aria-modal="true"` correctos, pero:

- **Falta `aria-labelledby`** apuntando al `<h2>{{ titulo() }}</h2>` (agregar `id` al `<h2>`
  y referenciarlo desde el `<div class="dialog">`).
- **Cero manejo de foco**: sin mover el foco al diálogo al abrirlo, sin `FocusTrap` (el foco
  puede escaparse del modal con Tab), sin devolución de foco al elemento que lo abrió al
  cerrarlo.
- **Sin `Escape` para cerrar** (debe emitir `cancelar`, igual que el botón "Cancelar").

Implementación: instalar `@angular/cdk` (ver sección de infraestructura) y usar
`cdk/a11y` (`ConfigurableFocusTrapFactory` o el directive `cdkTrapFocus`) + un
`@HostListener('keydown.escape')` en `confirm-dialog.ts`. Guardar `document.activeElement`
al abrir (mejor en el componente padre que lo instancia, ya que el propio diálogo no controla
su ciclo de vida de creación/destrucción) y devolver el foco ahí al cerrar.

Consumidores a validar tras el cambio: `features/backoffice/avisos/avisos.view.ts/.html`,
`features/backoffice/polizas/poliza-backoffice-detalle.view.ts/.html`.

### 2. `reportar-siniestro.view.html` — error de formulario no vinculado por campo

Único formulario del proyecto con `aria-invalid` **sin** `aria-describedby` — el mensaje de
error es único y genérico para todo el formulario (`role="alert"`, sin `id`), así que ningún
campo queda vinculado a su motivo de error específico (rompe el patrón ya establecido en
`login`/`registro`).

Implementación: replicar el patrón canónico (ver arriba) — un `id` de mensaje de error por
campo, referenciado desde el `aria-describedby` de su `<input>`/`<select>` correspondiente,
en vez del mensaje único genérico.

### 3. `avisos.view.html:176` — fila seleccionable sin tecla Space

`<tr>` con `tabindex="0"` + `(click)` + `(keydown.enter)`, pero sin `(keydown.space)` — el
estándar ARIA de activación por teclado para un elemento con rol interactivo exige ambas
teclas (Enter y Space).

Implementación: agregar `(keydown.space)="onSeleccionar($event)"` con
`$event.preventDefault()` (Space por defecto hace scroll de página), reusando el mismo
handler que ya usa `(keydown.enter)`.

### 4. 14 vistas sin ningún `aria-` — triage, no blanket fix

Incluyen listas reales (`polizas-lista`, `siniestros-lista`, `clientes.view`,
`cotizaciones.view`) y la vista de detalle de back-office de HU-60
(`poliza-backoffice-detalle.view.html`). **No se asume que todas necesitan el mismo
tratamiento** — antes de tocar cada una:

- Si es una tabla de datos: confirmar si ya usa `<table>`/`<th scope="col">` semántico (si
  usa `<div>` con grid de CSS en vez de tabla real, es un hueco real que vale la pena cerrar
  con roles ARIA de tabla — `role="table"`/`role="row"`/`role="cell"` — o migrar a `<table>`
  real si el diseño lo permite).
- Si es una vista de solo lectura simple (ej. un detalle sin interacción compleja): el hueco
  es menor, prioridad baja.
- `poliza-backoffice-detalle.view.html` (HU-60, recién construida) debería revisarse primero
  por ser la más nueva y la que mezcla lectura + formulario de coberturas + acciones.

Esta tarea requiere una pasada de lectura archivo por archivo antes de escribir el fix —
no se estima el esfuerzo aquí hasta hacer ese triage.

### 5. Infraestructura de verificación (previene regresiones futuras)

- **`@angular/cdk`**: instalar (ya se necesita para la tarea 1). Trae `cdk/a11y`
  (`LiveAnnouncer` para anunciar cambios dinámicos a lectores de pantalla — útil para
  estados de carga/éxito que hoy solo se muestran visualmente — y `FocusTrap`/
  `FocusMonitor`) y `cdk/overlay` si a futuro se necesita un modal más complejo.
- **Testing automatizado con axe**: el proyecto usa Playwright real (no Cypress), así que la
  herramienta correcta es `@axe-core/playwright`, no `cypress-axe` (que el proyecto de
  referencia tampoco tenía, para que quede claro que no se está replicando nada de ahí).
  Agregar un step/helper de Cucumber que corra un chequeo de axe contra la página actual en
  los escenarios E2E críticos (login, registro, cotizar, emitir, el modal de confirm-dialog
  una vez corregido) — no necesariamente en todos los escenarios existentes, empezar por los
  de mayor tráfico real.
- **Lint**: el proyecto no tiene ningún ESLint configurado (ni siquiera reglas base, no solo
  de a11y) — fuera de alcance de este plan agregar un linter completo desde cero, pero si se
  agrega en el futuro, debería incluir reglas de accesibilidad de Angular ESLint
  (`@angular-eslint/template/...`) para no volver a introducir regresiones del tipo "div
  clickeable"/"input sin label".
- **Documentación de contraste**: `styles.css` global solo tiene variables de color sin
  ratios documentados, sin soporte de `prefers-reduced-motion`/`prefers-contrast`. No incluido
  como tarea de código en este plan (es más una auditoría de diseño que de ingeniería) —
  dejar como nota para quien maneje el design system, no bloquea el resto del plan.

## Fuera de alcance (explícitamente)

- Rehacer `styles.css`/design tokens para documentar contraste — nota para diseño, no tarea
  de este plan.
- Agregar un linter completo nuevo al proyecto — mencionado como oportunidad futura, no se
  construye aquí.
- Cambiar el patrón de i18n de `| translate` a `i18n-*` nativo — el patrón actual ya es
  correcto para este stack, no es un hueco de accesibilidad.
- Tocar el proyecto de referencia (`MISW4104_202512_E04`) de ninguna forma — es de otro curso,
  se usó solo como punto de comparación.

## Verificación

```bash
cd apps/web
pnpm test          # Karma, debe seguir en 100% cobertura tras cada tarea
pnpm e2e            # Cucumber + Playwright, suite completa (no solo los escenarios nuevos)
```

Para el chequeo de axe nuevo (tarea 5), una vez instalado: correrlo contra un dev server real
levantado (`pnpm start`), no solo contra mocks, para capturar problemas de contraste/DOM real
que un mock no reproduce.

## Progreso

- [x] Investigación del proyecto de referencia (sin nada replicable como sistema).
- [x] Auditoría del estado real de `apps/web/` (base más madura de lo esperado).
- [x] Este documento.
- [x] **Tarea 1**: `confirm-dialog` — `aria-labelledby`/`aria-describedby`, `cdkTrapFocus` +
      `cdkTrapFocusAutoCapture` (`@angular/cdk/a11y`, en vez de la factory manual
      sugerida originalmente — más simple, mismo resultado), `Escape` vía `HostListener`.
      Devolución de foco (`core/a11y/focus-restore.ts`, nuevo) implementada en ambos
      consumidores reales: `poliza-backoffice-detalle.view.ts` (en la vista) y
      `avisos.viewmodel.ts` (en el viewmodel — decisión de diseño distinta entre los dos
      componentes, ambas válidas, no se unificó por no ser necesario).
- [x] **Tarea 2**: `reportar-siniestro.view.html` — patrón canónico `aria-describedby`/`id`
      por campo, mensajes de error específicos en vez del genérico único.
- [x] **Tarea 3**: `avisos.view.ts` — `(keydown.space)` ya estaba en el componente (con
      `preventDefault` para no hacer scroll), confirmado al revisar.
- [x] **Tarea 4**: triage completo. La mayoría de las 14 vistas originales ya tenían `aria-`
      desde antes (recibieron mejoras puntuales); solo `app.html`/`section.view.html`
      (shell raíz, stub genérico) quedan sin ningún `aria-`, dejados deliberadamente por
      bajo riesgo real.
- [x] **Tarea 5**: `@angular/cdk` + `@axe-core/playwright` instalados.
      `e2e/support/a11y.ts`/`e2e/steps/a11y.steps.ts` (`color-contrast` excluido a
      propósito, es auditoría de diseño). Conectado a 5 escenarios E2E críticos: login
      (3 escenarios), registro, cotizar, cancelación de póliza (incluyendo el
      `confirm-dialog` abierto Y cerrado, validando el fix del modal), firma de asesor.
- [x] Commit `b1da466` (rama `feature/accesibilidad-web`, basada en `develop` tras el merge
      de R6/#169). 464/464 Karma, 100% cobertura (4 ejes).

## Siguiente paso

- [ ] **Validar el E2E real con axe contra el stack Docker completo.** Se intentó correr
      `pnpm e2e` contra el dev server de Angular (`:4200`) y falló por `ERR_CONNECTION_REFUSED`
      en `:8080` — el E2E real espera `bff-web` (y el resto del stack) sirviendo ahí, no el
      dev server solo. Pendiente de levantar el stack completo (`docker compose`/build real,
      mismo patrón que otras validaciones E2E de esta sesión) y confirmar que los 5
      escenarios con el step de axe pasan sin violaciones reales.
- [ ] Abrir el PR contra `develop` una vez validado el E2E real.
