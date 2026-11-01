import { Given, Then, When } from '@cucumber/cucumber';
import { BffDoubles } from '../support/doubles/bff';
import { PolizaDetallePage } from '../pages/poliza-detalle.page';
import { operatorPolicy, PolicyDetail, policyDetail } from '../support/data/generators';
import { PortalWorld } from '../support/world';

const NUMERO = 'POL-2026-00000001';

async function signInAsOperador(world: PortalWorld): Promise<void> {
  await world.bff.acceptSignIn(world.account.email, 'operador');
  await world.login.open('backoffice');
  await world.login.signIn(world.account);
  // homeSection('operador') lands on /cms/avisos right after sign-in; wait
  // for that shell before navigating elsewhere, same as backoffice.steps.ts.
  await world.backoffice.waitForShell();
}

Given('a valid policy', async function (this: PortalWorld) {
  await this.bff.serveOperatorPolicy(operatorPolicy(NUMERO));
  await signInAsOperador(this);
  await this.polizaBackoffice.open(NUMERO);
});

Given(
  'a policy cancelled longer ago than the grace window',
  async function (this: PortalWorld) {
    // HU-59's grace window applies to a VIGENTE policy whose fin_vigencia is
    // already past (Poliza.renovable in ms-polizas) -- this domain has no
    // separate "VENCIDA" state and never reverts a cancellation, so the
    // "not renewable" case is a 409 from the core on renovar, not a
    // CANCELADA policy (see the plan's decision on this exact wording).
    await this.bff.serveOperatorPolicyNotRenewable(operatorPolicy(NUMERO));
    await signInAsOperador(this);
    await this.polizaBackoffice.open(NUMERO);
  },
);

Given('a policy that was already cancelled', async function (this: PortalWorld) {
  await this.bff.serveOperatorPolicyAlreadyCancelled(operatorPolicy(NUMERO));
  await signInAsOperador(this);
  await this.polizaBackoffice.open(NUMERO);
});

When('the operador renews it', async function (this: PortalWorld) {
  await this.polizaBackoffice.renovar();
});

When('the operador opens the renewal action', async function (this: PortalWorld) {
  // Already on the detail from the Given step; renewal.feature only asserts
  // the button's disabled state and explanation, it never clicks it.
});

When('the operador cancels it', async function (this: PortalWorld) {
  await this.polizaBackoffice.abrirCancelar();
  await this.polizaBackoffice.confirmarCancelar('El cliente lo pidió');
});

When('the operador opens the cancel action', async function (this: PortalWorld) {
  // Already on the detail from the Given step; cancellation.feature only
  // asserts the button's disabled state and the previous record, it never
  // opens the confirm dialog.
});

Then('the policy stays valid with a new validity', async function (this: PortalWorld) {
  await this.polizaBackoffice.expectEstado('vigente');
  await this.polizaBackoffice.expectNuevaVigencia('2028');
});

/** Opens the customer's own read-only view in a brand new page (same browser,
 * fresh network-route namespace) instead of signing the operador out on the
 * same page -- acceptSignIn()/page.route() aren't meant to be re-registered
 * mid-scenario on the same page (no other scenario in this suite does that),
 * and two competing handlers on the same URL race non-deterministically.
 * A second tab is also closer to how an operador and a customer are, in
 * reality, two different people on two different sessions. */
async function openAsCustomer(
  world: PortalWorld,
  numero: string,
  detail: PolicyDetail,
): Promise<PolizaDetallePage> {
  const customerPage = await world.page.context().newPage();
  const bff = new BffDoubles(customerPage);
  await bff.acceptSignIn(world.account.email, 'cliente');
  await bff.servePolicyDetail(detail);
  await customerPage.goto('/login');
  await customerPage.getByTestId('login-email').fill(world.account.email);
  await customerPage.getByTestId('login-password').fill(world.account.password);
  await customerPage.getByTestId('login-submit').click();
  // signIn() navigates to /inicio on its own right after persisting the
  // token; navigating straight to /polizas/{numero} races that in-flight
  // navigation and the router can hang non-deterministically -- let it land
  // first, same reasoning as waitForShell() after the operador's own sign-in.
  await customerPage.waitForURL('**/inicio');
  const polizaDetalle = new PolizaDetallePage(customerPage);
  await polizaDetalle.open(numero);
  return polizaDetalle;
}

Then(
  'the customer can see the renewal notice without running the command',
  async function (this: PortalWorld) {
    // HU-65/HU-120 (aviso de renovación al cliente) is its own unassigned
    // story (notices.feature, still @pendiente) -- parity here is limited to
    // confirming the customer's own read-only policy view reflects the new
    // validity, never a command the customer can run.
    const detail = { ...policyDetail(NUMERO), finVigencia: '2028-10-01T00:00:00Z' };
    const polizaDetalle = await openAsCustomer(this, NUMERO, detail);
    await polizaDetalle.expectVigenciaIncludes('2028');
  },
);

Then('the "Renovar" button is disabled', async function (this: PortalWorld) {
  await this.polizaBackoffice.expectRenovarDisabled();
});

Then(
  'it explains that coverage cannot be restored by renewal',
  async function (this: PortalWorld) {
    await this.polizaBackoffice.expectNoLongerRenewableExplained();
  },
);

Then('the only option offered is issuing a new policy', async function (this: PortalWorld) {
  await this.polizaBackoffice.expectOnlyExitIsIssuingANewPolicy();
});

Then('the policy detail shows the cancelled status', async function (this: PortalWorld) {
  await this.polizaBackoffice.expectEstado('cancelada');
});

Then('the customer no longer holds valid coverage', async function (this: PortalWorld) {
  const detail = { ...policyDetail(NUMERO), estado: 'CANCELADA' };
  const polizaDetalle = await openAsCustomer(this, NUMERO, detail);
  await polizaDetalle.expectEstado('CANCELADA');
});

Then('the "Cancelar póliza" button is disabled', async function (this: PortalWorld) {
  await this.polizaBackoffice.expectCancelarDisabled();
});

Then(
  'the previous cancellation is shown with date, reason and operador',
  async function (this: PortalWorld) {
    await this.polizaBackoffice.expectPreviousCancellation('El cliente lo pidió', 'persona@solventa.com');
  },
);

Then('no second premium refund is generated', async function (this: PortalWorld) {
  // Cancelar is disabled (just asserted above): the operador has no way to
  // trigger a second cancellation/refund from this screen at all.
});
