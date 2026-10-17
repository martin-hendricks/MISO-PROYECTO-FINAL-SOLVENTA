import { Given, Then, When } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

Given('the customer login page is open', async function (this: PortalWorld) {
  await this.login.open('customer');
  await this.login.expectVisible('customer');
});

Given('the customer is signed in', async function (this: PortalWorld) {
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.login.open('customer');
  await this.login.signIn(this.account);
  await this.shell.expectUserShell();
});

When('the customer signs in with valid credentials', async function (this: PortalWorld) {
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.login.signIn(this.account);
});

When('the customer signs in with invalid credentials', async function (this: PortalWorld) {
  await this.bff.rejectSignIn();
  await this.login.signIn(this.account);
});

When('the customer signs in while the network is down', async function (this: PortalWorld) {
  await this.bff.dropSignIn();
  await this.login.signIn(this.account);
});

When('the customer opens the login page', async function (this: PortalWorld) {
  await this.login.open('customer');
});

Then('the customer login view is visible', async function (this: PortalWorld) {
  await this.login.expectVisible('customer');
});

Then(
  'the login view shows the {word} error without leaving',
  async function (this: PortalWorld, kind: 'credentials' | 'network') {
    await this.login.expectError(kind);
    await this.login.expectVisible('customer');
  },
);
