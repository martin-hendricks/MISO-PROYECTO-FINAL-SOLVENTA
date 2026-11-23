import { Given, Then, When } from '@cucumber/cucumber';
import { emptyHome } from '../support/data/generators';
import { PortalWorld } from '../support/world';

const DOS = {
  moneda: 'COP',
  totalRecibido: 1070000,
  movimientos: [
    {
      id: '7b0c0000-0000-4000-8000-000000000001',
      siniestroId: 'SIN-1988',
      tipo: 'asistido',
      ramo: 'Protección de dispositivo',
      resumen: 'hurto',
      poliza: 'POL-88219-CO',
      monto: 890000,
      moneda: 'COP',
      comprobante: 'CMP-3F9A0C12DE',
      depositadoEn: '2026-07-11T15:20:00+00:00',
    },
    {
      id: 'a51e0000-0000-4000-8000-000000000002',
      siniestroId: 'SIN-1002',
      tipo: 'pago_automatico',
      ramo: 'Clima y vuelos',
      resumen: 'retraso de vuelo',
      poliza: 'POL-11002-CO',
      monto: 180000,
      moneda: 'COP',
      comprobante: 'CMP-0A77B2C4F1',
      depositadoEn: '2026-07-02T09:05:00+00:00',
    },
  ],
};

async function entrar(world: PortalWorld): Promise<void> {
  await world.bff.acceptSignIn(world.account.email, 'cliente');
  await world.bff.serveHome(emptyHome());
  await world.login.open('customer');
  await world.login.signIn(world.account);
  await world.page.waitForURL('**/inicio');
}

Given('the customer has two deposits', async function (this: PortalWorld) {
  await this.bff.serveWallet(DOS);
  await entrar(this);
});

Given('the customer has no deposits', async function (this: PortalWorld) {
  await this.bff.serveWallet({ moneda: 'COP', totalRecibido: 0, movimientos: [] });
  await entrar(this);
});

Given('the wallet read fails', async function (this: PortalWorld) {
  await this.bff.failWallet();
  await entrar(this);
});

When('the customer opens the wallet', async function (this: PortalWorld) {
  await this.billetera.open();
});

When('the customer retries the wallet', async function (this: PortalWorld) {
  await this.bff.serveWallet(DOS);
  await this.billetera.retry();
});

Then('the wallet shows both deposits and the total', async function (this: PortalWorld) {
  await this.billetera.expectTotal();
});

Then(
  'the wallet explains that a deposit appears when Solventa pays',
  async function (this: PortalWorld) {
    await this.billetera.expectEmpty();
  },
);

Then('the wallet offers a retry and no zero total', async function (this: PortalWorld) {
  await this.billetera.expectRetry();
});
