import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';
import { emptyHome, fullHome } from '../support/data/generators';
import { PortalWorld } from '../support/world';

Given('the portal is open', async function (this: PortalWorld) {
  await this.shell.open();
});

Then('the customer lands on Inicio', async function (this: PortalWorld) {
  await this.shell.expectInicio();
});

When('the customer opens Inicio', async function (this: PortalWorld) {
  this.home = fullHome();
  await this.bff.serveHome(this.home);
  await this.inicio.open();
});

Given('a valid offer on Inicio', async function (this: PortalWorld) {
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.serveHome(emptyHome());
  await this.login.open('customer');
  await this.login.signIn(this.account);
  await this.shell.expectInicio();
  this.home = fullHome();
  await this.bff.serveHome(this.home);
  await this.bff.watchQuotes();
  await this.inicio.open();
});

Then(
  'the customer sees the valid offer card when a quote can be consulted again',
  async function (this: PortalWorld) {
    const offer = this.home.ofertaVigente!;
    await this.inicio.expectCard('offer', offer.ramo);
    await this.inicio.expectLink('inicio-accept', `/emision/${offer.cotizacionId}`);
  },
);

Then(
  'the customer sees a shortcut to the policy detail when there is a valid policy',
  async function (this: PortalWorld) {
    const policy = this.home.poliza!;
    await this.inicio.expectCard('policy', policy.numero);
    await this.inicio.expectLink('inicio-policy-link', `/polizas/${policy.numero}`);
  },
);

Then(
  'the customer sees a shortcut to the open claim when there is one',
  async function (this: PortalWorld) {
    const claim = this.home.siniestroEnCurso!;
    await this.inicio.expectCard('claim', claim.siniestroId);
    await this.inicio.expectLink('inicio-claim-link', `/siniestros/${claim.siniestroId}`);
  },
);

Then(
  'the customer sees the Vida Crediticia card when there is an origination',
  async function (this: PortalWorld) {
    await this.inicio.expectCard('vida-crediticia', 'Vida Crediticia');
    await this.inicio.expectLink('inicio-vida-link', '/vida-crediticia');
  },
);

Then('"Nueva cotización" is below "Aceptar oferta"', async function (this: PortalWorld) {
  await this.inicio.expectQuoteBelowAccept();
});

Then('accepting starts the issuance, not a recalculation', async function (this: PortalWorld) {
  await this.inicio.accept();
  await this.inicio.expectIssuance(this.home.ofertaVigente!.cotizacionId);
  assert.equal(this.bff.quotesRequested(), 0);
});
