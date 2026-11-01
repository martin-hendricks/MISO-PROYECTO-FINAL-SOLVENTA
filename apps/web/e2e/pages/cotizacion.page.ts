import assert from 'node:assert/strict';
import { Page } from 'playwright';
import { Offer } from '../support/data/generators';

/** Customer and advisor quote screens, and the offer by id (HU-104, HU-113, HU-10). */
export class CotizacionPage {
  constructor(private readonly page: Page) {}

  async openNew(): Promise<void> {
    await this.page.goto('/cotizacion');
    await this.waitForCatalog();
  }

  async openAdvisor(): Promise<void> {
    await this.page.goto('/cms/cotizaciones/nueva');
    await this.waitForCatalog();
  }

  async openOffer(cotizacionId: string): Promise<void> {
    await this.page.goto(`/cotizaciones/${cotizacionId}`);
    await this.page
      .locator('[data-testid="ver-oferta"]:not([data-state="loading"])')
      .waitFor({ state: 'visible' });
  }

  /** The device form is the first one; its brand select fills once the catalog answers. */
  private async waitForCatalog(): Promise<void> {
    await this.page.locator('[data-testid="riesgo-marca"] option[value="apple"]').waitFor({
      state: 'attached',
    });
  }

  async lines(): Promise<{ label: string; disabled: boolean }[]> {
    return this.page
      .getByTestId('cotizacion-ramo')
      .locator('option')
      .evaluateAll((options) =>
        (options as HTMLOptionElement[]).map((o) => ({
          label: o.textContent!.replace(/\s+/g, ' ').trim(),
          disabled: o.disabled,
        })),
      );
  }

  async selectedLine(): Promise<string> {
    return this.page.getByTestId('cotizacion-ramo').inputValue();
  }

  async pickLine(id: string): Promise<void> {
    await this.page.getByTestId('cotizacion-ramo').selectOption(id);
  }

  async fillDevice(): Promise<void> {
    await this.page.getByTestId('riesgo-valorDispositivo').fill('2400000');
    await this.page.getByTestId('riesgo-marca').selectOption('apple');
    await this.page.getByTestId('riesgo-modelo').fill('iPhone 15');
    await this.page.getByTestId('riesgo-masDe12Meses-no').check();
  }

  async fillClient(nombre: string, documento: string): Promise<void> {
    await this.page.getByTestId('cliente-nombre').fill(nombre);
    await this.page.getByTestId('cliente-documento').fill(documento);
  }

  async fillSoat(cilindraje: string): Promise<void> {
    await this.page.getByTestId('riesgo-placa').waitFor({ state: 'visible' });
    await this.page.getByTestId('riesgo-placa').fill('ABC12D');
    await this.page.getByTestId('riesgo-cilindraje_cc').fill(cilindraje);
    await this.page.getByTestId('riesgo-modelo_anio').fill('2022');
    await this.page.getByTestId('riesgo-ciudad_circulacion').selectOption('cali');
  }

  /** Mortgage life (HU-58): its fields render once the `Vida hipotecario` catalog answers. */
  async fillMortgage(valor = '180000000', plazoMeses = '240'): Promise<void> {
    await this.page.getByTestId('riesgo-valorCredito').fill(valor);
    await this.page.getByTestId('riesgo-plazoMeses').fill(plazoMeses);
    await this.page.locator('.hint', { hasText: 'Entre 6 y 360' }).waitFor({ state: 'visible' });
  }

  async consentProfiling(checked = true): Promise<void> {
    await this.page.getByTestId('asesor-consentimiento').setChecked(checked);
  }

  async typeEngine(cilindraje: string): Promise<void> {
    await this.page.getByTestId('riesgo-cilindraje_cc').fill(cilindraje);
  }

  async quote(): Promise<void> {
    await this.page.getByTestId('cotizar').click();
  }

  async calculate(): Promise<void> {
    await this.page.getByTestId('calcular').click();
  }

  async cancelHref(): Promise<string | null> {
    return this.page.getByTestId('cancelar').getAttribute('href');
  }

  async isCalculateDisabled(): Promise<boolean> {
    return this.page.getByTestId('calcular').isDisabled();
  }

  async fieldError(clave: string): Promise<string> {
    const error = this.page.getByTestId(`riesgo-${clave}-error`);
    await error.waitFor({ state: 'visible' });
    return (await error.textContent())!.trim();
  }

  async value(testId: string): Promise<string> {
    return this.page.getByTestId(testId).inputValue();
  }

  async expectNoOffer(): Promise<void> {
    await this.page.getByTestId('sin-oferta').waitFor({ state: 'visible' });
  }

  /** The firm offer as the customer offer screen or the advisor panel shows it. */
  async expectOffer(offer: Offer): Promise<void> {
    const prima = this.page.getByTestId('oferta-prima');
    await prima.waitFor({ state: 'visible' });
    const amount = Number(offer.prima).toLocaleString('es-CO', { maximumFractionDigits: 0 });
    assert.ok((await prima.textContent())?.includes(amount), `premium should show ${amount}`);
  }

  async expectOfferDetails(offer: Offer): Promise<void> {
    await this.expectOffer(offer);
    assert.equal((await this.page.getByTestId('oferta-moneda').textContent())?.trim(), 'COP');
    const vence = await this.page.getByTestId('oferta-vence').textContent();
    assert.ok(vence?.includes(String(new Date(offer.venceEn).getFullYear())), 'expiry shown');
  }

  async expectOfferId(cotizacionId: string): Promise<void> {
    assert.equal((await this.page.getByTestId('oferta-id').textContent())?.trim(), cotizacionId);
  }

  async acceptHref(): Promise<string | null> {
    return this.page.getByTestId('oferta-aceptar').getAttribute('href');
  }

  async expectOfferPath(cotizacionId: string): Promise<void> {
    await this.page.waitForURL(`**/cotizaciones/${cotizacionId}`);
  }
}
