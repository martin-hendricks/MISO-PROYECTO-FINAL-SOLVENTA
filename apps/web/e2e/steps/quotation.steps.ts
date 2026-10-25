import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';
import { CATALOGS, clients, emptyHome, offer } from '../support/data/generators';
import { PortalWorld } from '../support/world';

async function signInCustomer(world: PortalWorld): Promise<void> {
  await world.bff.acceptSignIn(world.account.email, 'cliente');
  await world.bff.serveHome(emptyHome());
  await world.login.open('customer');
  await world.login.signIn(world.account);
  await world.shell.expectInicio();
}

async function signInAdvisor(world: PortalWorld): Promise<void> {
  world.clientes = clients(5);
  await world.bff.serveClients(world.clientes);
  await world.bff.acceptSignIn(world.account.email, 'asesor');
  await world.login.open('backoffice');
  await world.login.signIn(world.account);
  await world.backoffice.waitForShell();
}

// Customer quote (HU-104)

Given('the customer is on Inicio or uses the header CTA', async function (this: PortalWorld) {
  this.offer = offer();
  await this.bff.serveCatalogs('cliente', CATALOGS);
  await this.bff.serveQuote('cliente', this.offer);
  await signInCustomer(this);
  assert.equal(await this.page.getByTestId('header-new-quote').getAttribute('href'), '/cotizacion');
});

When('the customer opens a new quote', async function (this: PortalWorld) {
  await this.cotizacion.openNew();
});

Then(
  'the customer picks the line, starting on Protección de dispositivo',
  async function (this: PortalWorld) {
    assert.equal(await this.cotizacion.selectedLine(), 'dispositivo');
  },
);

Then(
  'the lines the core does not quote yet are disabled as Próximamente',
  async function (this: PortalWorld) {
    const lines = await this.cotizacion.lines();
    assert.deepEqual(
      lines.filter((line) => !line.disabled).map((line) => line.label),
      ['Protección de dispositivo', 'SOAT motocicleta'],
    );
    assert.equal(lines.filter((line) => line.label.endsWith('· Próximamente')).length, 5);
  },
);

Then('"Cotizar" goes to the offer with premium and expiry', async function (this: PortalWorld) {
  await this.cotizacion.fillDevice();
  await this.cotizacion.quote();
  await this.cotizacion.expectOfferPath(this.offer.cotizacionId);
  await this.cotizacion.expectOfferDetails(this.offer);
  assert.deepEqual(this.bff.quoteBody(), {
    ramo: 'Protección de dispositivo',
    datosRiesgo: {
      valorDispositivo: 2400000,
      marca: 'apple',
      modelo: 'iPhone 15',
      masDe12Meses: false,
    },
  });
});

Then('"Cancelar" returns to Inicio', async function (this: PortalWorld) {
  await this.cotizacion.openNew();
  assert.equal(await this.cotizacion.cancelHref(), '/inicio');
});

// View offer (HU-113)

Given('a valid quote id', async function (this: PortalWorld) {
  this.offer = offer();
  await this.bff.serveQuote('cliente', this.offer);
  await signInCustomer(this);
});

When('the customer opens the offer', async function (this: PortalWorld) {
  await this.cotizacion.openOffer(this.offer.cotizacionId);
});

Then('the customer sees premium, currency and expiry', async function (this: PortalWorld) {
  await this.cotizacion.expectOfferDetails(this.offer);
});

Then('consulting it again does not recalculate', async function (this: PortalWorld) {
  await this.cotizacion.openOffer(this.offer.cotizacionId);
  await this.cotizacion.expectOfferDetails(this.offer);
  assert.equal(this.bff.offersRead(), 2);
  assert.equal(this.bff.quotesRequested(), 0);
});

Then('"Aceptar" starts the issuance', async function (this: PortalWorld) {
  assert.equal(
    await this.cotizacion.acceptHref(),
    `/emision?cotizacion=${this.offer.cotizacionId}`,
  );
});

// Advisor quote (HU-10)

Given('the catalog of a line of business', async function (this: PortalWorld) {
  this.offer = offer();
  await this.bff.serveCatalogs('asesor', CATALOGS);
  await this.bff.serveQuote('asesor', this.offer);
  await signInAdvisor(this);
});

When('the asesor sends the product and the minimum risk data', async function (this: PortalWorld) {
  await this.cotizacion.openAdvisor();
  await this.cotizacion.fillClient('Andrés Gómez', '1020334556');
  await this.cotizacion.fillDevice();
  await this.cotizacion.calculate();
});

Then('the asesor gets a quote id and sees the firm offer', async function (this: PortalWorld) {
  await this.cotizacion.expectOffer(this.offer);
  await this.cotizacion.expectOfferId(this.offer.cotizacionId);
  assert.equal(this.bff.quoteBody()?.['clienteId'], '1020334556');
});

// The advisor keeps the offer in the panel by its id; the core calculated it once.
Then('consulting it again by id does not recalculate', async function (this: PortalWorld) {
  await this.cotizacion.expectOfferId(this.offer.cotizacionId);
  assert.equal(this.bff.quotesRequested(), 1);
});

Given('the asesor capturing a SOAT motorcycle quote', async function (this: PortalWorld) {
  await this.bff.serveCatalogs('asesor', CATALOGS);
  await signInAdvisor(this);
  await this.cotizacion.openAdvisor();
  await this.cotizacion.fillClient('Andrés Gómez', '1020334556');
  await this.cotizacion.pickLine('soat');
  await this.cotizacion.fillSoat('150');
});

When(
  'the asesor types an engine size out of the allowed range',
  async function (this: PortalWorld) {
    await this.cotizacion.typeEngine('2500');
  },
);

Then('the field is marked as an error with the valid range', async function (this: PortalWorld) {
  assert.match(await this.cotizacion.fieldError('cilindraje_cc'), /entre 50 y 1800/);
});

Then('the "Calcular prima" button is disabled', async function (this: PortalWorld) {
  assert.ok(await this.cotizacion.isCalculateDisabled());
});

Then(
  'the offer panel shows "Sin oferta" without losing the captured data',
  async function (this: PortalWorld) {
    await this.cotizacion.expectNoOffer();
    assert.equal(await this.cotizacion.value('cliente-nombre'), 'Andrés Gómez');
    assert.equal(await this.cotizacion.value('riesgo-cilindraje_cc'), '2500');
  },
);
