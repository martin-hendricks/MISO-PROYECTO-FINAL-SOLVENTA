import { After, Before } from '@cucumber/cucumber';
import { PortalWorld } from './world';

Before(async function (this: PortalWorld) {
  await this.openBrowser();
});

After(async function (this: PortalWorld) {
  await this.closeBrowser();
});
