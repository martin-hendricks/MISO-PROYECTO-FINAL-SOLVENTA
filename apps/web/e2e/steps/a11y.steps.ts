import { Then } from '@cucumber/cucumber';
import { expectSinViolacionesDeAccesibilidad } from '../support/a11y';
import { PortalWorld } from '../support/world';

Then('the current page has no accessibility violations', async function (this: PortalWorld) {
  await expectSinViolacionesDeAccesibilidad(this.page);
});
