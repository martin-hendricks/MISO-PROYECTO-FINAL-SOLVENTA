import assert from 'node:assert/strict';
import { Page } from 'playwright';

export class PolizasAvisosPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/polizas/avisos');
    await this.page
      .locator('[data-testid="avisos-polizas"]:not([data-state="loading"])')
      .waitFor({ state: 'visible' });
  }

  async expectNoticeFor(numero: string): Promise<void> {
    await this.page.getByTestId(`aviso-${numero}`).waitFor({ state: 'visible' });
  }

  async expectNoRenewAction(): Promise<void> {
    const buttons = await this.page.locator('[data-testid="avisos-list"] button').count();
    assert.equal(buttons, 0, 'expected no renew action on the read-only expiry notice');
  }
}
