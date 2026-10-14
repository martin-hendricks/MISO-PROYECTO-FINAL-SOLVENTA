import { Given, Then, When } from '@cucumber/cucumber';
import { Section } from '../pages/backoffice.page';
import { clients } from '../support/data/generators';
import { Role } from '../support/doubles/bff';
import { PortalWorld } from '../support/world';

Given('the BFF lists {int} clients', async function (this: PortalWorld, count: number) {
  this.clientes = clients(count);
  await this.bff.serveClients(this.clientes);
});

Given('the BFF has no clients', async function (this: PortalWorld) {
  this.clientes = [];
  await this.bff.serveClients(this.clientes);
});

Given('the BFF fails to list clients', async function (this: PortalWorld) {
  await this.bff.failClients();
});

Given('an {word} signed in to the back-office', async function (this: PortalWorld, role: Role) {
  if (!this.bff.hasClients()) {
    this.clientes = clients(5);
    await this.bff.serveClients(this.clientes);
  }
  await this.bff.acceptSignIn(this.account.email, role);
  await this.login.open('backoffice');
  await this.login.signIn(this.account);
  await this.backoffice.waitForShell();
});

When('the visitor opens the back-office', async function (this: PortalWorld) {
  await this.backoffice.open();
});

When('the user opens the {word} destination', async function (this: PortalWorld, name: Section) {
  await this.backoffice.openSection(name);
});

When('the user signs out of the back-office', async function (this: PortalWorld) {
  await this.backoffice.signOut();
});

When('the user goes back from the no-permission state', async function (this: PortalWorld) {
  await this.backoffice.goHomeFromNoPermission();
});

When('the asesor retries loading the clients', async function (this: PortalWorld) {
  await this.backoffice.retryClients();
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

Then('the client list shows the listed clients', async function (this: PortalWorld) {
  await this.backoffice.expectClients(this.clientes);
});

Then(
  'the client list shows the {word} state',
  async function (this: PortalWorld, state: 'empty' | 'error') {
    await this.backoffice.expectClientsState(state);
  },
);

Then(
  'the content says the role {word} needs the role {word}',
  async function (this: PortalWorld, current: Role, required: Role) {
    await this.backoffice.expectNoPermission(current, required);
  },
);

Then('the back-office login is visible', async function (this: PortalWorld) {
  await this.login.expectVisible('backoffice');
});
