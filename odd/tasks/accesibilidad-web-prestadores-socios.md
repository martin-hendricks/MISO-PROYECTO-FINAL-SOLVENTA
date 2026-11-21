# Accesibilidad web: prestadores y socios

## Objetivo

Cerrar los huecos de accesibilidad de las vistas de prestadores (cliente y back-office) y de
socios, agregadas después de `accesibilidad-web-completar` (PR #213), y cubrirlas con axe en
e2e.

## Línea base (no se toca)

- Planes anteriores: `accesibilidad-web` (`b1da466`) y `accesibilidad-web-completar` (#213).
- Ya correcto en lo nuevo: la tarjeta de prestador mueve el foco al abrir, cierra con Escape y
  devuelve el foco; chips del cliente con `aria-pressed`; lista de pines como alternativa al
  mapa; tablas con `caption` y `th scope`; vista previa de idioma/región con `aria-live`.
- Los diálogos de confirmación de prestadores y socios no necesitan devolución de foco manual:
  `cdkTrapFocusAutoCapture` la hace al cerrar y sus disparadores siguen en pantalla al cancelar.

## Problema (auditado el 2026-11-21 contra `develop` en `4ad6f41f`)

| Vista | Hueco |
| --- | --- |
| Formulario de prestador (back-office) | Con el mapa disponible se ocultan latitud y longitud y el pin solo se mueve arrastrando: sin alternativa para quien no usa mouse (WCAG 2.5.7). |
| Formulario de prestador (back-office) | Chips de ramos sin `aria-pressed`; el error de ramos no está ligado al grupo. |
| Mapa de prestadores del cliente | Botón de cada fila sin `aria-expanded`/`aria-controls`. Mensajes de vacío, sin geolocalización, ciudad bloqueada y país sin datos sin `role="status"`. |
| Mapa de prestadores del cliente | Enlaces `target="_blank"` ("Cómo llegar") sin aviso de pestaña nueva. |
| Socios | Nombre del formulario sin `aria-required`; "Copiar" cambia de texto sin anunciarlo. |
| E2E | Cinco `.feature` sin axe: back-office prestadores, socios, cerca del siniestro, mapa cliente, idioma/región. |

## Alcance

Dentro: `apps/web/src/app/features/{backoffice/prestadores,backoffice/socios,prestadores}`,
las 4 traducciones `core/i18n/es-{CO,MX,CL,PE}.json`, specs Karma de lo tocado y los
`.feature` listados.

Fuera: contraste, `prefers-reduced-motion`, linter, paridad Android.

## Tareas

| ID | Tarea |
| --- | --- |
| T1 | Formulario de prestador: latitud/longitud siempre visibles; `aria-pressed` en chips; `aria-describedby` del grupo hacia el error de ramos. |
| T2 | Mapa del cliente: `aria-expanded`/`aria-controls` en filas; `role="status"` en los 4 mensajes; aviso "se abre en una pestaña nueva" en "Cómo llegar" (lista y tarjeta). |
| T3 | Socios: `aria-required` en el nombre; región `role="status"` que anuncia "Copiada". |
| T4 | E2E: step de axe en 9 escenarios de los 5 `.feature`. |

## Criterios de aceptación

- [x] `pnpm test` en verde: 678/678, cobertura 100% (4 ejes).
- [x] `pnpm build` sin errores.
- [x] `pnpm e2e` de los escenarios tocados en verde con axe: 20 de 20 (prestadores + idioma/región
      18, socios 2), contra el build de producción.

## Limitaciones conocidas

- El formulario de prestador y la vista del mapa del cliente no tienen spec Karma de vista
  (solo e2e). T1 y T2 se verifican con axe y con la revisión de plantilla; los atributos de T2
  que viven en esas vistas no tienen test unitario propio.
- El e2e corre sin clave de Google Maps, así que axe audita la variante sin mapa. El caso
  "mapa disponible" del formulario (latitud/longitud junto al pin) no lo cubre ningún test.

## Progreso

- [x] T1 a T3 implementadas; T3 y el aviso de pestaña nueva de la tarjeta con test Karma.
- [x] T4: axe agregado.
- [x] e2e de los 5 `.feature` en verde. No se corrió la suite completa.
