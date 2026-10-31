import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

Given('a first-time visitor opens the portal', async function (this: PortalWorld) {
  // HU-108's gate is only on sign-up ("Continuar sigue a registro"), not on
  // "/" or "/login" -- a returning customer going straight to /login to
  // sign in is not a "first launch". Each scenario opens a fresh browser
  // context (hooks.ts): localStorage starts empty, so requireLocaleChosen
  // on /registro already sends this navigation to idioma-region.
  await this.page.goto('/registro');
});

When('the visitor reaches idioma-region', async function (this: PortalWorld) {
  await this.idiomaRegion.expectVisibleAtTopLevel();
});

Then(
  'the visitor can choose Español Colombia, México, Chile or Perú',
  async function (this: PortalWorld) {
    await this.idiomaRegion.expectOptions();
  },
);

Then('Continuar goes to sign-up, not a permissions splash', async function (this: PortalWorld) {
  await this.idiomaRegion.continueToSignUp();
  await this.page.getByTestId('registro-form').waitFor({ state: 'visible' });
  assert.equal(new URL(this.page.url()).pathname, '/registro');
});

When(
  'the visitor chooses Español México and continues',
  async function (this: PortalWorld) {
    await this.idiomaRegion.choose('es-MX');
    await this.idiomaRegion.continueToSignUp();
  },
);

Then('the sign-up view is shown in the chosen locale', async function (this: PortalWorld) {
  await this.page.getByTestId('registro-form').waitFor({ state: 'visible' });
  assert.equal(new URL(this.page.url()).pathname, '/registro');
  const lang = await this.page.evaluate(() => localStorage.getItem('solventa.locale'));
  assert.equal(lang, 'es-MX');
});

When('the customer opens idioma y región from Perfil', async function (this: PortalWorld) {
  await this.idiomaRegion.openFromPerfil();
});

Then('the dialog closes with Listo', async function (this: PortalWorld) {
  await this.idiomaRegion.closeWithDone();
});

Then(
  'the customer is not sent to sign-up or data consent',
  async function (this: PortalWorld) {
    const pathname = new URL(this.page.url()).pathname;
    assert.ok(
      pathname !== '/registro' && pathname !== '/consentimiento',
      `expected to stay away from sign-up/consent, got ${pathname}`,
    );
  },
);
