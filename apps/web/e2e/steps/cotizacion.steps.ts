import { Then, When } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

When('the advisor starts a new quote', async function (this: PortalWorld) {
  await this.cotizacion.openNew();
});

When(
  'the advisor fills the quote for a device worth {word}',
  async function (this: PortalWorld, valorAsegurado: string) {
    await this.cotizacion.fill(valorAsegurado);
  },
);

When('the advisor calculates the premium', async function (this: PortalWorld) {
  await this.cotizacion.calculate();
});

Then(
  'the firm offer shows the premium {string}',
  async function (this: PortalWorld, prima: string) {
    await this.cotizacion.expectOffer(prima);
  },
);

Then('the advisor can continue to issuance', async function (this: PortalWorld) {
  await this.cotizacion.expectIssuance();
});

Then(
  'the quote was priced {int} time and read by id {int} time',
  function (this: PortalWorld, priced: number, readById: number) {
    this.cotizacion.expectRequests(priced, readById);
  },
);

Then('the insured value shows its valid range', async function (this: PortalWorld) {
  await this.cotizacion.expectValueRange();
});

Then('the premium cannot be calculated', async function (this: PortalWorld) {
  await this.cotizacion.expectCalculateDisabled();
});

Then('the offer panel says there is no offer', async function (this: PortalWorld) {
  await this.cotizacion.expectNoOffer();
});

Then('the quote keeps the captured client', async function (this: PortalWorld) {
  await this.cotizacion.expectClientKept();
});
