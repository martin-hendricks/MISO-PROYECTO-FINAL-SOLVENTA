import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';
import { emptyHome, fullHome, policyDetail } from '../support/data/generators';
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
    await this.inicio.expectLink('inicio-accept', `/emision?cotizacion=${offer.cotizacionId}`);
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

Given('the customer is signed in on a 1440 canvas', async function (this: PortalWorld) {
  await this.setCanvasWidth(1440);
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.serveHome(emptyHome());
  await this.login.open('customer');
  await this.login.signIn(this.account);
  await this.shell.expectInicio();
});

Then(
  'the top navigation shows Inicio, Pólizas, Siniestros and Perfil as text',
  async function (this: PortalWorld) {
    await this.shell.expectDesktopDestinations();
  },
);

Then(
  '"Nueva cotización" is a filled button, not an underlined destination',
  async function (this: PortalWorld) {
    await this.shell.expectNewQuoteIsAFilledButtonNotADestination();
  },
);

Given('the customer is on a 390 canvas', async function (this: PortalWorld) {
  await this.setCanvasWidth(390);
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.serveHome(emptyHome());
  await this.login.open('customer');
  await this.login.signIn(this.account);
  await this.shell.expectInicio();
});

When('the customer opens the menu', async function (this: PortalWorld) {
  await this.shell.openMenu();
});

Then('the navigation menu shows the same four destinations', async function (this: PortalWorld) {
  await this.shell.expectMenuShowsFourDestinations();
});

Then('closing the overlay does not change the page', async function (this: PortalWorld) {
  const urlBeforeClose = this.page.url();
  await this.shell.closeMenuOverlay();
  await this.shell.expectMenuClosed();
  assert.equal(this.page.url(), urlBeforeClose);
});

Given('the customer is on the policy detail', async function (this: PortalWorld) {
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.serveHome(emptyHome());
  await this.login.open('customer');
  await this.login.signIn(this.account);
  await this.shell.expectInicio();
  const detail = policyDetail('POL-00001-CO');
  await this.bff.servePolicyDetail(detail);
  await this.bff.servePolicyList([detail]);
  await this.polizaDetalle.open(detail.numero);
});

Then('the Pólizas destination stays underlined', async function (this: PortalWorld) {
  await this.shell.expectPolizasDestinationUnderlined();
});

Then(
  '"Volver" returns to the policy list, not to Inicio',
  async function (this: PortalWorld) {
    await this.polizaDetalle.goBack();
    assert.equal(new URL(this.page.url()).pathname, '/polizas');
  },
);

Given('the customer accepted a valid offer', async function (this: PortalWorld) {
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.serveHome(emptyHome());
  await this.login.open('customer');
  await this.login.signIn(this.account);
  await this.shell.expectInicio();
  this.home = fullHome();
  await this.bff.serveHome(this.home);
  await this.inicio.open();
  await this.inicio.accept();
});

When('the customer is on Emitiendo or Póliza emitida', async function (this: PortalWorld) {
  await this.inicio.expectIssuance(this.home.ofertaVigente!.cotizacionId);
});

Then('the customer cannot change destination', async function (this: PortalWorld) {
  await this.shell.expectNoDestinationIsClickable();
});
