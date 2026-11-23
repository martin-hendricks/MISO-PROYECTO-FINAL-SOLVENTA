import { Given, Then, When } from '@cucumber/cucumber';
import { signUp } from '../support/data/generators';
import { PortalWorld } from '../support/world';

Given('a customer ready to register monthly amounts', async function (this: PortalWorld) {
  await this.registro.assumeLocaleAlreadyChosen();
  await this.registro.open();
});

When(
  'the customer registers, quotes, confirms the local card and issues',
  async function (this: PortalWorld) {
    await this.registro.fill(signUp());
    await this.cotizacion.openCard('COT-1042');
    await this.cotizacion.fillCard();
    await this.cotizacion.confirmCard();
  },
);

Then(
  'the issued policy offers automatic renewal without sending the card',
  async function (this: PortalWorld) {
    await this.page.getByTestId('renovacion-automatica').waitFor({ state: 'visible' });
    const body = this.bff.signUpRequest();
    const serialized = JSON.stringify(body ?? {});
    if (serialized.includes('4242')) {
      throw new Error('card digits must stay out of Solventa requests');
    }
  },
);
