import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';
import {
  CATALOGS,
  clients,
  fullHome,
  MortgageOffer,
  mortgageOffer,
} from '../support/data/generators';
import { PortalWorld } from '../support/world';

/** The same offer when the profiling stub failed: fallback premium, no factors (HU-56). */
function degraded(offer: unknown): MortgageOffer {
  return { ...(offer as MortgageOffer), factores: [], degradada: true };
}

// Mortgage life offer of the customer (HU-105)

Given('an active origination and profiling consent', async function (this: PortalWorld) {
  this.offer = mortgageOffer();
  this.home = fullHome();
  await this.bff.serveCatalogs('cliente', CATALOGS);
  await this.bff.serveMortgageOffer('cliente', this.offer as MortgageOffer);
  await this.bff.serveMortgageOrigination({ valor: 180000000, plazoMeses: 240 });
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.serveHome(this.home);
  await this.login.open('customer');
  await this.login.signIn(this.account);
  await this.shell.expectInicio();
});

When('the customer opens the Vida Crediticia card', async function (this: PortalWorld) {
  await this.inicio.open();
  await this.page.getByTestId('inicio-vida-link').click();
  await this.vidaCrediticia.waitForConsent();
  await this.vidaCrediticia.authorize();
});

Then(
  'the customer sees the mortgage offer with premium and internal factors',
  async function (this: PortalWorld) {
    await this.cotizacion.expectOffer(this.offer);
    await this.vidaCrediticia.expectFactor('Zona de riesgo');
    assert.deepEqual(this.bff.mortgageBody(), {
      credito: { valor: 180000000, plazoMeses: 240 },
      consentimientoPerfil: true,
    });
  },
);

Then(
  'if the stub failed the customer sees the degradation banner',
  async function (this: PortalWorld) {
    await this.bff.serveMortgageOffer('cliente', degraded(this.offer));
    await this.vidaCrediticia.open();
    await this.vidaCrediticia.authorize();
    await this.vidaCrediticia.expectDegraded();
  },
);

Then('Perfil does not start this flow', async function (this: PortalWorld) {
  assert.equal(await this.page.getByTestId('nav-perfil').getAttribute('href'), '/perfil');
});

// Advisor mortgage offer (HU-58)

Given('a profile built by Solventa', async function (this: PortalWorld) {
  this.offer = mortgageOffer();
  this.clientes = clients(5);
  await this.bff.serveCatalogs('asesor', CATALOGS);
  await this.bff.serveMortgageOffer('asesor', this.offer as MortgageOffer);
  await this.bff.serveClients(this.clientes);
  await this.bff.acceptSignIn(this.account.email, 'asesor');
  await this.login.open('backoffice');
  await this.login.signIn(this.account);
  await this.backoffice.waitForShell();
});

When('the mortgage asesor opens the offer in the portal', async function (this: PortalWorld) {
  await this.cotizacion.openAdvisor();
  await this.cotizacion.fillClient('Ricardo Salas', '80112334');
  await this.cotizacion.pickLine('hipotecario');
  await this.cotizacion.fillMortgage();
  await this.cotizacion.consentProfiling();
  await this.cotizacion.calculate();
});

Then(
  'the asesor sees premium and internal factors without leaving the flow',
  async function (this: PortalWorld) {
    await this.cotizacion.expectOffer(this.offer);
    const factores = await this.page.getByTestId('oferta-factores').textContent();
    assert.ok(factores?.includes('Zona de riesgo'), 'factors should show Zona de riesgo');
    assert.equal(new URL(this.page.url()).pathname, '/cms/cotizaciones/nueva');
    assert.equal(this.bff.mortgageBody()?.['clienteId'], '80112334');
  },
);

Then('if the stub failed the asesor sees the fallback value', async function (this: PortalWorld) {
  await this.bff.serveMortgageOffer('asesor', degraded(this.offer));
  // Withdrawing and giving the consent again drops the offer on screen, so it is requested anew.
  await this.cotizacion.consentProfiling(false);
  await this.cotizacion.consentProfiling();
  await this.cotizacion.calculate();
  await this.page.getByTestId('oferta-degradada').waitFor({ state: 'visible' });
});

Then('this view is not the customer Vida Crediticia card', async function (this: PortalWorld) {
  assert.equal(await this.page.getByTestId('vida-crediticia').count(), 0);
  assert.ok(new URL(this.page.url()).pathname.startsWith('/cms/'));
});

// Acceptance after revoking the profiling consent (HU-165)

Given("a mortgage offer quoted with the customer's profile", async function (this: PortalWorld) {
  this.offer = mortgageOffer();
  this.home = fullHome();
  await this.bff.serveCatalogs('cliente', CATALOGS);
  await this.bff.serveMortgageOffer('cliente', this.offer as MortgageOffer);
  await this.bff.serveMortgageOrigination(null);
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.serveHome(this.home);
  await this.login.open('customer');
  await this.login.signIn(this.account);
  await this.shell.expectInicio();
  await this.vidaCrediticia.open();
  await this.vidaCrediticia.authorize();
});

Given('the customer then revoked the profiling consent', async function (this: PortalWorld) {
  await this.bff.refuseIssuance(422, {
    codigo: 'consentimiento_revocado',
    mensaje: 'El consentimiento de perfilamiento ya no está vigente; vuelva a cotizar',
  });
});

When('the customer accepts the mortgage offer', async function (this: PortalWorld) {
  await this.page.getByTestId('oferta-aceptar').click();
  await this.cotizacion.fillCard();
  await this.cotizacion.confirmCard();
});

Then('the customer is told the profiling consent was revoked', async function (this: PortalWorld) {
  const aviso = this.page.getByTestId('emision-revoked');
  await aviso.waitFor({ state: 'visible' });
  assert.ok(
    (await aviso.textContent())?.includes('Revocaste la autorización para usar tus datos en el perfilamiento.'),
  );
  assert.equal(this.bff.issuesRequested(), 1);
});

Then('the customer can start a new quote instead of retrying', async function (this: PortalWorld) {
  assert.equal(await this.page.getByTestId('emision-revoked-new-quote').getAttribute('href'), '/cotizacion');
  assert.equal(await this.page.getByTestId('emision-retry').count(), 0);
});

// Mortgage life from Nueva cotización

Given('a customer on Nueva cotización', async function (this: PortalWorld) {
  this.offer = mortgageOffer();
  await this.bff.serveCatalogs('cliente', CATALOGS);
  await this.bff.serveMortgageOffer('cliente', this.offer as MortgageOffer);
  await this.bff.serveMortgageOrigination(null);
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.serveHome(fullHome());
  await this.login.open('customer');
  await this.login.signIn(this.account);
  await this.shell.expectInicio();
  await this.cotizacion.openNew();
});

When('the customer quotes Vida hipotecario', async function (this: PortalWorld) {
  await this.cotizacion.pickLine('hipotecario');
  await this.cotizacion.fillMortgage('180000000', '240');
  await this.page.getByTestId('cotizar').click();
});

Then(
  'the mortgage is saved and the consent opens with the amounts filled',
  async function (this: PortalWorld) {
    await this.page.waitForURL('**/vida-crediticia?**');
    await this.vidaCrediticia.waitForConsent();
    await this.vidaCrediticia.expectPrefilled('180000000', '240');
    assert.deepEqual(this.bff.originationBody(), { valor: 180000000, plazoMeses: 240 });
    assert.equal(this.bff.quotesRequested(), 0);
  },
);

Then('authorizing shows each profiling step before the offer', async function (this: PortalWorld) {
  await this.vidaCrediticia.authorizePrefilled();
  await this.vidaCrediticia.expectProfilingSteps();
  await this.vidaCrediticia.expectFactor('Zona de riesgo');
  assert.deepEqual(this.bff.mortgageBody(), {
    credito: { valor: 180000000, plazoMeses: 240 },
    consentimientoPerfil: true,
  });
});
