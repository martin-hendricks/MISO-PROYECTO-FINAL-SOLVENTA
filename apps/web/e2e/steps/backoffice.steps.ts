import { Given, Then, When } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

type StaffRole = 'asesor' | 'operador';
type Section = 'clientes' | 'cotizaciones' | 'polizas' | 'avisos';

Given(
  'an {word} signed in to the back-office',
  async function (this: PortalWorld, role: StaffRole) {
    await this.backoffice.signInAs(role);
  },
);

When('the visitor opens the back-office', async function (this: PortalWorld) {
  await this.backoffice.open();
});

When('the user opens the {word} destination', async function (this: PortalWorld, name: Section) {
  await this.backoffice.openSection(name);
});

When('the user signs out of the back-office', async function (this: PortalWorld) {
  await this.backoffice.signOut();
});

Then('the back-office shows its four destinations', async function (this: PortalWorld) {
  await this.backoffice.expectShell();
});

Then(
  'the {word} destination is the current one',
  async function (this: PortalWorld, name: Section) {
    await this.backoffice.expectCurrentSection(name);
  },
);

Then('the client list shows {int} clients', async function (this: PortalWorld, count: number) {
  await this.backoffice.expectClients(count);
});

Then(
  'the content says the role {word} needs the role {word}',
  async function (this: PortalWorld, current: StaffRole, required: StaffRole) {
    await this.backoffice.expectNoPermission(current, required);
  },
);

Then('the back-office login is visible', async function (this: PortalWorld) {
  await this.backoffice.expectLogin();
});
