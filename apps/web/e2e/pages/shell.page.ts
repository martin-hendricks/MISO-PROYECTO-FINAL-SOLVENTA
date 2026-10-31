import assert from 'node:assert/strict';
import { Page } from 'playwright';

export class ShellPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/');
  }

  async expectInicio(): Promise<void> {
    await this.page.getByTestId('inicio').waitFor({ state: 'visible' });
  }

  async expectDesktopDestinations(): Promise<void> {
    for (const testId of ['nav-inicio', 'nav-polizas', 'nav-siniestros', 'nav-perfil']) {
      await this.page.getByTestId(testId).waitFor({ state: 'visible' });
    }
    await this.page.getByTestId('nav-menu-toggle').waitFor({ state: 'hidden' });
  }

  async expectNewQuoteIsAFilledButtonNotADestination(): Promise<void> {
    const cta = this.page.getByTestId('header-new-quote');
    assert.equal(await cta.evaluate((el) => el.classList.contains('active')), false);
  }

  async openMenu(): Promise<void> {
    await this.page.getByTestId('nav-menu-toggle').click();
  }

  async closeMenuOverlay(): Promise<void> {
    await this.page.getByTestId('nav-menu-close').click();
  }

  async expectMenuShowsFourDestinations(): Promise<void> {
    const overlay = this.page.getByTestId('nav-menu-overlay');
    await overlay.waitFor({ state: 'visible' });
    for (const testId of [
      'nav-menu-inicio',
      'nav-menu-polizas',
      'nav-menu-siniestros',
      'nav-menu-perfil',
    ]) {
      await overlay.getByTestId(testId).waitFor({ state: 'visible' });
    }
  }

  async expectMenuClosed(): Promise<void> {
    await this.page.getByTestId('nav-menu-overlay').waitFor({ state: 'hidden' });
  }

  async expectPolizasDestinationUnderlined(): Promise<void> {
    const link = this.page.getByTestId('nav-polizas');
    assert.equal(await link.evaluate((el) => el.classList.contains('active')), true);
  }

  /** Issuance (/emision) lives outside sv-shell-layout in app.routes.ts --
   * no TopNav is ever rendered there, so there is nothing to click. */
  async expectNoDestinationIsClickable(): Promise<void> {
    for (const testId of ['nav-inicio', 'nav-polizas', 'nav-siniestros', 'nav-perfil']) {
      assert.equal(await this.page.getByTestId(testId).count(), 0);
    }
  }
}
