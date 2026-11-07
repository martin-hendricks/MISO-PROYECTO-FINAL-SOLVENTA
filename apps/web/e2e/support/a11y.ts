import assert from 'node:assert/strict';
import AxeBuilder from '@axe-core/playwright';
import { Page } from 'playwright';

/** Color contrast is a design-system audit, explicitly out of scope for this
 * plan (see odd/tasks/accesibilidad-web.md); every other axe rule stays on. */
const REGLAS_FUERA_DE_ALCANCE = ['color-contrast'];

/** Fails the scenario with the concrete axe findings when the current page
 * (and whatever modal is open on it) has accessibility violations. */
export async function expectSinViolacionesDeAccesibilidad(page: Page): Promise<void> {
  const { violations } = await new AxeBuilder({ page })
    .disableRules(REGLAS_FUERA_DE_ALCANCE)
    .analyze();
  const detalle = violations
    .map(
      (violacion) =>
        `${violacion.id} (${violacion.impact}): ${violacion.nodes
          .map((nodo) => nodo.target.join(' '))
          .join(', ')}`,
    )
    .join('\n');
  assert.equal(violations.length, 0, `axe encontró violaciones de accesibilidad:\n${detalle}`);
}
