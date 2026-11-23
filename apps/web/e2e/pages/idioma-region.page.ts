import assert from 'node:assert/strict';
import { Page } from 'playwright';

export class IdiomaRegionPage {
  constructor(private readonly page: Page) {}

  async expectVisibleAtTopLevel(): Promise<void> {
    await this.page.getByTestId('idioma-region').waitFor({ state: 'visible' });
    assert.equal(new URL(this.page.url()).pathname, '/idioma-region');
  }

  async expectOptions(): Promise<void> {
    for (const locale of ['es-CO', 'es-MX', 'es-CL', 'es-PE']) {
      await this.page.getByTestId(`idioma-region-${locale}`).waitFor({ state: 'visible' });
    }
  }

  async choose(locale: 'es-CO' | 'es-MX' | 'es-CL' | 'es-PE'): Promise<void> {
    await this.page.getByTestId(`idioma-region-${locale}`).click();
  }

  /** Sample premium/date preview, with Intl's (narrow) NBSPs normalized. */
  async samplePreview(): Promise<{ premium: string; date: string }> {
    const read = async (id: string) =>
      (await this.page.getByTestId(id).innerText()).replace(/[  ]/g, ' ').trim();
    return {
      premium: await read('idioma-region-sample-premium'),
      date: await read('idioma-region-sample-date'),
    };
  }

  async continueToSignUp(): Promise<void> {
    await this.page.getByTestId('idioma-region-continue').click();
  }

  async openFromPerfil(): Promise<void> {
    await this.page.goto('/perfil');
    await this.page.getByTestId('perfil-idioma-region-open').click();
  }

  async closeWithDone(): Promise<void> {
    const dialog = this.page.getByTestId('idioma-region');
    await dialog.waitFor({ state: 'visible' });
    await this.page.getByTestId('idioma-region-done').click();
    await dialog.waitFor({ state: 'hidden' });
  }
}
