import assert from 'node:assert/strict';
import { Page } from 'playwright';

export type InicioCard = 'offer' | 'policy' | 'claim' | 'vida-crediticia';

export class InicioPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/inicio');
    await this.page
      .locator('[data-testid="inicio"]:not([data-state="loading"])')
      .waitFor({ state: 'visible' });
  }

  async expectCard(card: InicioCard, text: string): Promise<void> {
    const element = this.page.getByTestId(`inicio-${card}`);
    await element.waitFor({ state: 'visible' });
    assert.ok((await element.textContent())?.includes(text), `${card} should show ${text}`);
  }

  async expectLink(testId: string, href: string): Promise<void> {
    assert.equal(await this.page.getByTestId(testId).getAttribute('href'), href);
  }

  async expectQuoteBelowAccept(): Promise<void> {
    const accept = await this.page.getByTestId('inicio-accept').boundingBox();
    const quote = await this.page.getByTestId('inicio-new-quote').boundingBox();
    assert.ok(accept && quote, 'both actions should be on screen');
    assert.ok(quote.y >= accept.y + accept.height, '"Nueva cotización" should be below Aceptar');
  }

  async accept(): Promise<void> {
    await this.page.getByTestId('inicio-accept').click();
  }

  /** Issuance takes only the quote id (HU-149): bff-web creates the offer id on acceptance. */
  async expectIssuance(cotizacionId: string): Promise<void> {
    await this.page.getByTestId('emision').waitFor({ state: 'visible' });
    const url = new URL(this.page.url());
    assert.equal(url.pathname, '/emision');
    assert.equal(url.searchParams.get('cotizacion'), cotizacionId);
  }
}
