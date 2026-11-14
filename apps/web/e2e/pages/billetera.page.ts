import assert from 'node:assert/strict';
import { Page } from 'playwright';

export class BilleteraPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/billetera');
    await this.page
      .locator('[data-testid="billetera"]:not([data-state="loading"])')
      .waitFor({ state: 'visible' });
  }

  async expectTotal(): Promise<void> {
    const total = this.page.getByTestId('billetera-total');
    await total.waitFor({ state: 'visible' });
    assert.match((await total.textContent()) ?? '', /1\.070\.000/);
    assert.equal(await this.page.getByTestId('billetera-fila').count(), 2);
    const table = await this.page.getByTestId('billetera-table').textContent();
    assert.match(table ?? '', /890\.000/);
    assert.match(table ?? '', /180\.000/);
  }

  async expectEmpty(): Promise<void> {
    await this.page.getByTestId('billetera-vacia').waitFor({ state: 'visible' });
    assert.equal(
      await this.page.getByTestId('billetera-ver-siniestros').getAttribute('href'),
      '/siniestros',
    );
    assert.equal(await this.page.getByTestId('billetera-total').count(), 0);
  }

  async expectRetry(): Promise<void> {
    await this.page.getByTestId('billetera-reintentar').waitFor({ state: 'visible' });
    assert.equal(await this.page.getByTestId('billetera-total').count(), 0);
  }

  async retry(): Promise<void> {
    await this.page.getByTestId('billetera-reintentar').click();
    await this.page.getByTestId('billetera-total').waitFor({ state: 'visible' });
  }
}
