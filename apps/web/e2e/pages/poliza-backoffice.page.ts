import assert from 'node:assert/strict';
import { Page } from 'playwright';

export class PolizaBackofficePage {
  constructor(private readonly page: Page) {}

  async open(numero: string): Promise<void> {
    await this.page.goto(`/cms/polizas/${numero}`);
    await this.page
      .locator('[data-testid="poliza-backoffice"]:not([data-state="loading"])')
      .waitFor({ state: 'visible' });
  }

  async renovar(): Promise<void> {
    const response = this.page.waitForResponse((res) => res.url().includes('/operador/polizas/ciclo'));
    await this.page.getByTestId('poliza-backoffice-renovar').click();
    await response;
  }

  async expectRenovarDisabled(): Promise<void> {
    assert.equal(await this.page.getByTestId('poliza-backoffice-renovar').isDisabled(), true);
  }

  async expectNoLongerRenewableExplained(): Promise<void> {
    await this.page.getByTestId('poliza-backoffice-no-renovable').waitFor({ state: 'visible' });
  }

  async expectOnlyExitIsIssuingANewPolicy(): Promise<void> {
    assert.equal(await this.page.getByTestId('poliza-backoffice-cancelar').isDisabled(), false);
  }

  async abrirCancelar(): Promise<void> {
    await this.page.getByTestId('poliza-backoffice-cancelar').click();
    await this.page.getByTestId('confirm-dialog').waitFor({ state: 'visible' });
  }

  async confirmarCancelar(motivo: string): Promise<void> {
    // The dialog closes as soon as it's confirmed, before the POST .../ciclo
    // response arrives (see confirmarCancelar() in the component) -- wait
    // for the response itself, not just the dialog closing, before moving on.
    const response = this.page.waitForResponse((res) => res.url().includes('/operador/polizas/ciclo'));
    await this.page.getByTestId('confirm-dialog-motivo').fill(motivo);
    await this.page.getByTestId('confirm-dialog-confirmar').click();
    await response;
    await this.page.getByTestId('confirm-dialog').waitFor({ state: 'detached' });
  }

  async expectEstado(estado: 'vigente' | 'cancelada'): Promise<void> {
    await this.page
      .locator(`[data-testid="poliza-backoffice-estado"][data-estado="${estado}"]`)
      .waitFor({ state: 'visible' });
  }

  async expectNuevaVigencia(fecha: string): Promise<void> {
    const locator = this.page.getByTestId('poliza-backoffice-vence');
    await locator.filter({ hasText: fecha }).waitFor({ state: 'visible' });
    assert.ok((await locator.innerText()).includes(fecha));
  }

  async expectCancelarDisabled(): Promise<void> {
    await this.page
      .locator('[data-testid="poliza-backoffice-cancelar"][disabled]')
      .waitFor({ state: 'visible' });
  }

  async expectPreviousCancellation(motivo: string, operador: string): Promise<void> {
    const registro = this.page.getByTestId('poliza-backoffice-cancelacion-previa');
    await registro.filter({ hasText: motivo }).waitFor({ state: 'visible' });
    const texto = await registro.innerText();
    assert.ok(texto.includes(operador), `expected cancellation record to include operador "${operador}"`);
  }
}
