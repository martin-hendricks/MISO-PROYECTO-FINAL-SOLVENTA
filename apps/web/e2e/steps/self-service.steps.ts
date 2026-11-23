import { Given, Then, When } from '@cucumber/cucumber';
import { policyDetail } from '../support/data/generators';
import { PortalWorld } from '../support/world';

const NUMERO = 'POL-2026-00000003';

Given('the customer is signed in with a valid policy', async function (this: PortalWorld) {
  await this.bff.acceptSignIn(this.account.email, 'cliente');
  await this.bff.servePolicyDetail(policyDetail(NUMERO));
  await this.login.open('customer');
  await this.login.signIn(this.account);
  // signIn() navega a /inicio por su cuenta justo después de persistir el
  // token -- entrar directo al detalle de la póliza corre contra esa
  // navegación en curso (mismo razonamiento documentado en policy-lifecycle
  // .steps.ts para openAsCustomer()/polizasAvisos.open()).
  await this.page.waitForURL('**/inicio');
});

When('the customer consults and manages the basics', async function (this: PortalWorld) {
  await this.polizaDetalle.open(NUMERO);
});

Then('the customer does not need an advisor', async function (this: PortalWorld) {
  // El detalle carga directo con la sesión del cliente, sin ningún paso
  // intermedio de asesor (ni asignación, ni aprobación) -- la URL y los
  // datos ya reflejan la póliza real del cliente.
  await this.polizaDetalle.expectEstado('VIGENTE');
});

Then('the customer cannot renew, modify or cancel a policy', async function (this: PortalWorld) {
  await this.polizaDetalle.expectNoLifecycleActions();
});
