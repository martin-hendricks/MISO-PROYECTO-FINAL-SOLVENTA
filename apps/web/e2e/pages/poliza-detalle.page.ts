import assert from 'node:assert/strict';
import { Page } from 'playwright';

export class PolizaDetallePage {
  constructor(private readonly page: Page) {}

  async open(numero: string): Promise<void> {
    await this.page.goto(`/polizas/${numero}`);
    await this.page
      .locator('[data-testid="poliza-detalle"]:not([data-state="loading"])')
      .waitFor({ state: 'visible' });
  }

  async expectEstado(estado: 'VIGENTE' | 'CANCELADA'): Promise<void> {
    assert.equal(await this.page.getByTestId('poliza-estado').getAttribute('data-estado'), estado);
  }

  async expectVigenciaIncludes(fecha: string): Promise<void> {
    const texto = await this.page.getByTestId('poliza-vigencia').innerText();
    assert.ok(texto.includes(fecha), `expected vigencia to include ${fecha}, got ${texto}`);
  }

  async goBack(): Promise<void> {
    await this.page.getByTestId('poliza-back').click();
    await this.page
      .locator('[data-testid="polizas-lista"]:not([data-state="loading"])')
      .waitFor({ state: 'visible' });
  }
}
