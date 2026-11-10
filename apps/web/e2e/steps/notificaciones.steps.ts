import { Given, Then, When } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

const ANA = '11111111-1111-4111-8111-111111111111';
const LUIS = '22222222-2222-4222-8222-222222222222';
const DIFUSION = 'c2d40000-0000-4000-8000-000000000001';

Given(
  'the operator directory lists Ana with a device and Luis without one',
  async function (this: PortalWorld) {
    this.clientes = [
      {
        clienteId: ANA,
        nombre: 'Ana Ruiz',
        documento: '10203040',
        canal: 'web',
        estado: 'activo',
        consentimiento: 'habeas_data',
      },
      {
        clienteId: LUIS,
        nombre: 'Luis Paz',
        documento: '50607080',
        canal: 'web',
        estado: 'activo',
        consentimiento: 'habeas_data',
      },
    ];
    await this.bff.serveDirectory([
      {
        usuarioId: ANA,
        nombre: 'Ana',
        apellidos: 'Ruiz',
        email: 'ana@correo.com',
        documento: '10203040',
        estado: 'ACTIVO',
        dispositivosActivos: 1,
      },
      {
        usuarioId: LUIS,
        nombre: 'Luis',
        apellidos: 'Paz',
        email: 'luis@correo.com',
        documento: '50607080',
        estado: 'ACTIVO',
        dispositivosActivos: 0,
      },
    ]);
  },
);

Then('Ana can receive push and Luis cannot', async function (this: PortalWorld) {
  await this.backoffice.expectCustomerPush(ANA, 'si');
  await this.backoffice.expectCustomerPush(LUIS, 'no');
});

Then('the operator can create a customer', async function (this: PortalWorld) {
  await this.backoffice.expectCanCreateCustomer();
});

Then('the customer list is visible', async function (this: PortalWorld) {
  await this.backoffice.expectClients(this.clientes);
});

Then('the customer write controls are hidden', async function (this: PortalWorld) {
  await this.backoffice.expectWriteControlsHidden(ANA);
});

Then('the Notificaciones destination is absent', async function (this: PortalWorld) {
  await this.backoffice.expectNotificacionesAbsent();
});

When('the user quotes Ana', async function (this: PortalWorld) {
  await this.backoffice.quoteCustomer(ANA);
});

Then('the advisor quote starts for Ana', async function (this: PortalWorld) {
  await this.backoffice.expectQuoteStarted(ANA);
});

Given('the broadcast audience includes Ana', async function (this: PortalWorld) {
  await this.bff.serveBroadcast([
    { usuarioId: ANA, nombre: 'Ana', apellidos: 'Ruiz', dispositivosActivos: 1 },
  ]);
});

Then('the broadcast form shows the title limit', async function (this: PortalWorld) {
  await this.notificaciones.expectForm();
});

When(
  'the operator writes {string} and {string}',
  async function (this: PortalWorld, titulo: string, cuerpo: string) {
    await this.notificaciones.write(titulo, cuerpo);
  },
);

Then('the broadcast preview mirrors that message', async function (this: PortalWorld) {
  await this.notificaciones.expectPreview('Mantenimiento', 'El domingo no habrá app');
});

When('the operator sends the broadcast', async function (this: PortalWorld) {
  await this.notificaciones.send();
});

Then('the broadcast result shows 2 sent', async function (this: PortalWorld) {
  await this.notificaciones.expectResult('2');
});

Then('the broadcast history includes {string}', async function (this: PortalWorld, titulo: string) {
  await this.notificaciones.expectHistory(DIFUSION, titulo);
});
