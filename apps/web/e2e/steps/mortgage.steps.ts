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
