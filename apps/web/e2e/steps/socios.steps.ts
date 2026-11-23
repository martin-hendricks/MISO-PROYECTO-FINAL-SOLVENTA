import { Given, Then, When } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

const API_KEY = 'sk_e2e_socio_nuevo';

Given('the BFF lists the partner {string}', async function (this: PortalWorld, nombre: string) {
  await this.bff.servePartners([nombre], API_KEY);
});

When(
  'the user creates the partner {string} with the scope {word}',
  async function (this: PortalWorld, nombre: string, alcance: string) {
    await this.backoffice.createPartner(nombre, alcance);
  },
);

When('the user dismisses the API key', async function (this: PortalWorld) {
  await this.backoffice.dismissApiKey();
});

Then('the partner {string} is listed', async function (this: PortalWorld, nombre: string) {
  await this.backoffice.expectPartner(nombre);
});

Then(
  'the partner {string} is listed as active without management options',
  async function (this: PortalWorld, nombre: string) {
    await this.backoffice.expectPartnerReadOnly(nombre);
  },
);

Then('the new API key is shown', async function (this: PortalWorld) {
  await this.backoffice.expectApiKey(API_KEY);
});

Then('the API key is no longer shown', async function (this: PortalWorld) {
  await this.backoffice.expectApiKeyHidden();
});
