import { Given, Then, When } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

Given('the portal is open', async function (this: PortalWorld) {
  await this.shell.open();
});

Then('the user shell is visible', async function (this: PortalWorld) {
  await this.shell.expectUserShell();
});

When('the visitor opens the CMS shell', async function (this: PortalWorld) {
  await this.shell.openCms();
});

Then('the CMS shell is visible', async function (this: PortalWorld) {
  await this.shell.expectCmsShell();
});
