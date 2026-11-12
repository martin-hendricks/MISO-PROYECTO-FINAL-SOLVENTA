import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

async function openPerfil(world: PortalWorld): Promise<void> {
  await world.bff.serveProfile(world.account.email);
  await world.page.goto('/perfil');
  await world.page.getByTestId('destino-perfil').waitFor({ state: 'visible' });
}

Given('the customer granted the profiling consent', async function (this: PortalWorld) {
  await this.bff.serveProfilingConsent('2026-10-01T10:00:00Z');
});

Given('the customer never granted the profiling consent', async function (this: PortalWorld) {
  await this.bff.serveProfilingConsent(null);
});

When('the customer opens Perfil', async function (this: PortalWorld) {
  await openPerfil(this);
});

When('the customer revokes the profiling consent from Perfil', async function (this: PortalWorld) {
  await openPerfil(this);
  await this.page.getByTestId('perfil-consentimiento-open').click();
  await this.page.getByTestId('confirm-dialog-confirmar').click();
  await this.page.getByTestId('confirm-dialog').waitFor({ state: 'hidden' });
});

When(
  'the customer opens the profiling consent from Perfil and cancels',
  async function (this: PortalWorld) {
    await openPerfil(this);
    await this.page.getByTestId('perfil-consentimiento-open').click();
    await this.page.getByTestId('confirm-dialog').waitFor({ state: 'visible' });
    await this.page.getByTestId('confirm-dialog-cancelar').click();
    await this.page.getByTestId('confirm-dialog').waitFor({ state: 'hidden' });
  },
);

Then('the revocation reaches the BFF once', async function (this: PortalWorld) {
  assert.equal(this.bff.profilingConsentRevoked(), 1);
});

Then('no revocation reaches the BFF', async function (this: PortalWorld) {
  assert.equal(this.bff.profilingConsentRevoked(), 0);
});

Then('Perfil shows the profiling consent as revoked', async function (this: PortalWorld) {
  const auditoria = this.page.getByTestId('perfil-consentimiento-auditoria');
  await auditoria.waitFor({ state: 'visible' });
  assert.match((await auditoria.textContent()) ?? '', /Revocado/);
  assert.equal(await this.page.getByTestId('perfil-consentimiento-open').isDisabled(), true);
});

Then(
  'Perfil still shows when the profiling consent was granted',
  async function (this: PortalWorld) {
    const auditoria = this.page.getByTestId('perfil-consentimiento-auditoria');
    assert.match((await auditoria.textContent()) ?? '', /Otorgado/);
    assert.equal(await this.page.getByTestId('perfil-consentimiento-open').isEnabled(), true);
  },
);

Then('Perfil does not list a profiling consent', async function (this: PortalWorld) {
  await this.page.getByTestId('perfil-nombre').waitFor({ state: 'visible' });
  assert.equal(await this.page.getByTestId('perfil-consentimiento').count(), 0);
});
