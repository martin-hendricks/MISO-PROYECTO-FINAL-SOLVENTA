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

  async expectIssuance(cotizacionId: string): Promise<void> {
    const destination = this.page.getByTestId('destino-emision');
    await destination.waitFor({ state: 'visible' });
    assert.equal(await destination.getAttribute('data-id'), cotizacionId);
    assert.equal(new URL(this.page.url()).pathname, `/emision/${cotizacionId}`);
  }
}
