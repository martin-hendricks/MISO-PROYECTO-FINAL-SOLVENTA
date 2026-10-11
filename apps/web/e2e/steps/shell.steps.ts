import { Given, Then } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

Given('the portal is open', async function (this: PortalWorld) {
  await this.shell.open();
});

Then('the user shell is visible', async function (this: PortalWorld) {
  await this.shell.expectUserShell();
});
