import { Given, Then, When } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

Given('the login page is open', async function (this: PortalWorld) {
  await this.login.open();
});

Given('the customer is signed in', async function (this: PortalWorld) {
  await this.login.acceptCredentials();
  await this.login.open();
  await this.login.signIn();
});

When('the customer signs in with valid credentials', async function (this: PortalWorld) {
  await this.login.acceptCredentials();
  await this.login.signIn();
});

When('the customer signs in with invalid credentials', async function (this: PortalWorld) {
  await this.login.rejectCredentials();
  await this.login.signIn();
});

When('the customer signs in while the network is down', async function (this: PortalWorld) {
  await this.login.dropConnection();
  await this.login.signIn();
});

Then('the login view is visible', async function (this: PortalWorld) {
  await this.login.expectVisible();
});

Then(
  'the login view shows the {word} error without leaving',
  async function (this: PortalWorld, kind: 'credentials' | 'network') {
    await this.login.expectError(kind);
    await this.login.expectStillOnLogin();
  },
);
