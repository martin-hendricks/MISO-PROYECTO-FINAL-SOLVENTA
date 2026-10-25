import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';
import { emptyHome, signUp } from '../support/data/generators';
import { PortalWorld } from '../support/world';

Given('the customer login page is open', async function (this: PortalWorld) {
  await this.login.open('customer');
  await this.login.expectVisible('customer');
});

Given('the customer is signed in', async function (this: PortalWorld) {
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.serveHome(emptyHome());
  await this.login.open('customer');
  await this.login.signIn(this.account);
  await this.shell.expectInicio();
});

When('the customer signs in with valid credentials', async function (this: PortalWorld) {
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.serveHome(emptyHome());
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

Given(
  'the customer comes from language and region or from "Crear cuenta" on login',
  async function (this: PortalWorld) {
    await this.registro.watchCamera();
    await this.login.open('customer');
    await this.registro.openFromLogin();
  },
);

Given('the customer is on sign-up', async function (this: PortalWorld) {
  await this.registro.open();
});

When(
  'the customer fills in name, document, email and password',
  async function (this: PortalWorld) {
    await this.registro.fill(signUp());
  },
);

When('the customer chooses to sign in', async function (this: PortalWorld) {
  await this.registro.chooseSignIn();
});

Then('the customer continues to data consent', async function (this: PortalWorld) {
  await this.registro.expectConsentStep();
});

Then('no document photo or biometrics are requested', async function (this: PortalWorld) {
  await this.registro.expectNoPhotoOrBiometrics();
});

Then('the customer goes to the web login', async function (this: PortalWorld) {
  await this.login.expectVisible('customer');
});

Given('the customer completed sign-up', async function (this: PortalWorld) {
  this.alta = signUp();
  await this.bff.acceptSignUp();
  await this.bff.serveHome(emptyHome());
  await this.registro.open();
  await this.registro.fill(this.alta);
  await this.registro.expectConsentStep();
});

When('the customer grants data processing consent', async function (this: PortalWorld) {
  await this.consentimiento.grant();
});

Then('the consent mark is auditable', async function (this: PortalWorld) {
  const { nombre, apellidos, documento, correo, contrasena } = this.alta;
  assert.deepEqual(this.bff.signUpRequest(), {
    nombre,
    apellidos,
    documento,
    correo,
    contrasena,
    habeasData: true,
  });
  const mark = this.bff.grantedConsent();
  assert.equal(mark?.habeasData, true);
  assert.ok(mark?.version, 'the mark names the policy version');
  assert.ok(!Number.isNaN(Date.parse(mark?.otorgadoEn ?? '')), 'the mark is dated');
});
