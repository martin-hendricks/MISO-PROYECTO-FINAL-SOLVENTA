import assert from 'node:assert/strict';
import { Page } from 'playwright';

/** Mortgage life origination of the customer (HU-105): consent, then the profiled offer. */
export class VidaCrediticiaPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/vida-crediticia');
    await this.waitForConsent();
  }

  /** The consent step is ready once the catalog bounds the mortgage data. */
  async waitForConsent(): Promise<void> {
    await this.page.getByTestId('vida-consentimiento').waitFor({ state: 'visible' });
    await this.page.locator('.hint', { hasText: 'Entre 6 y 360' }).waitFor({ state: 'visible' });
  }

  async authorize(valor = '180000000', plazoMeses = '240'): Promise<void> {
    if (await this.page.getByTestId('vida-valor').isEditable()) {
      await this.page.getByTestId('vida-valor').fill(valor);
      await this.page.getByTestId('vida-plazoMeses').fill(plazoMeses);
    }
    await this.page.getByTestId('vida-autorizar').click();
    await this.page.getByTestId('vida-factores').waitFor({ state: 'visible' });
  }

  async expectPrefilled(valor: string, plazoMeses: string): Promise<void> {
    assert.equal(await this.page.getByTestId('vida-valor').inputValue(), valor);
    assert.equal(await this.page.getByTestId('vida-plazoMeses').inputValue(), plazoMeses);
  }

  async authorizePrefilled(): Promise<void> {
    await this.page.getByTestId('vida-autorizar').click();
  }

  async expectProfilingSteps(): Promise<void> {
    await this.page.getByTestId('vida-progreso').waitFor({ state: 'visible' });
    for (const etapa of ['openFinance', 'openData', 'riesgo', 'oferta']) {
      await this.page.getByTestId(`vida-etapa-${etapa}`).waitFor({ state: 'visible' });
    }
    await this.page.getByTestId('vida-factores').waitFor({ state: 'visible' });
  }

  async expectFactor(nombre: string): Promise<void> {
    const factores = await this.page.getByTestId('vida-factores').textContent();
    assert.ok(factores?.includes(nombre), `factors should show ${nombre}`);
  }

  async expectDegraded(): Promise<void> {
    await this.page.getByTestId('vida-degradada').waitFor({ state: 'visible' });
  }
}
