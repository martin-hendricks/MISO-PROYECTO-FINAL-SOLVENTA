import { Page } from 'playwright';

export class PolizaDetallePage {
  constructor(private readonly page: Page) {}

  async open(numero: string): Promise<void> {
    await this.page.goto(`/polizas/${numero}`);
    await this.page
      .locator('[data-testid="poliza-detalle"]:not([data-state="loading"])')
      .waitFor({ state: 'visible' });
  }

  async goBack(): Promise<void> {
    await this.page.getByTestId('poliza-back').click();
    await this.page
      .locator('[data-testid="polizas-lista"]:not([data-state="loading"])')
      .waitFor({ state: 'visible' });
  }
}
