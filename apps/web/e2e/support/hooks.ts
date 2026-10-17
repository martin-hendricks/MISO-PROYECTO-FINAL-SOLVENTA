import { After, AfterStep, Before, setDefaultTimeout } from '@cucumber/cucumber';
import { reseed, SEED } from './data/generators';
import { PortalWorld } from './world';

setDefaultTimeout(15_000);

Before(async function (this: PortalWorld) {
  reseed();
  this.attach(`seed ${SEED}`);
  await this.openBrowser();
});

AfterStep(async function (this: PortalWorld) {
  this.attach(await this.page.screenshot({ fullPage: true }), 'image/png');
});

After(async function (this: PortalWorld) {
  await this.closeBrowser();
});
