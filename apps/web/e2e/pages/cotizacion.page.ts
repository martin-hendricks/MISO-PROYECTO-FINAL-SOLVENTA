import assert from 'node:assert/strict';
import { Page } from 'playwright';

const OFERTA = {
  cotizacionId: 'COT-1042',
  ramo: 'dispositivo',
  estado: 'oferta_vigente',
  prima: 89000,
  primaNeta: 72500,
  gastosExpedicion: 16500,
  moneda: 'COP',
  vigenciaMeses: 12,
  venceEn: '2026-10-01',
};
const CLIENTE = 'Andrés Gómez Molina';

export class CotizacionPage {
  private priced = 0;
  private readById = 0;

  constructor(private readonly page: Page) {}

  async openNew(): Promise<void> {
    await this.page.route('**/web/asesor/cotizaciones', (route) => {
      this.priced += 1;
      return route.fulfill({ json: OFERTA });
    });
    await this.page.route('**/web/asesor/cotizaciones/*', (route) => {
      this.readById += 1;
      return route.fulfill({ json: OFERTA });
    });
    await this.page.getByTestId('cotizaciones-new').click();
    await this.page.getByTestId('cotizacion-form').waitFor({ state: 'visible' });
    assert.equal(new URL(this.page.url()).pathname, '/cms/cotizaciones/nueva');
  }

  async fill(valorAsegurado: string): Promise<void> {
    await this.page.getByTestId('cotizacion-nombre').fill(CLIENTE);
    await this.page.getByTestId('cotizacion-documento').fill('1020334556');
    await this.page.getByTestId('cotizacion-valor').fill(valorAsegurado);
    await this.page.getByTestId('cotizacion-marca').fill('Samsung');
    await this.page.getByTestId('cotizacion-modelo').fill('Galaxy A54');
  }

  async calculate(): Promise<void> {
    await this.page.getByTestId('cotizacion-calcular').click();
    await this.page.locator('[data-testid="section-cotizacion"][data-state="ready"]').waitFor();
  }

  async expectOffer(prima: string): Promise<void> {
    const offer = this.page.getByTestId('cotizacion-oferta');
    await offer.waitFor({ state: 'visible' });
    assert.equal(await offer.getAttribute('data-cotizacion-id'), OFERTA.cotizacionId);
    assert.equal(await this.page.getByTestId('oferta-prima').innerText(), prima);
  }

  async expectIssuance(): Promise<void> {
    const href = await this.page.getByTestId('cotizacion-emitir').getAttribute('href');
    assert.equal(href, `/cms/polizas?cotizacion=${OFERTA.cotizacionId}`);
  }

  expectRequests(priced: number, readById: number): void {
    assert.deepEqual({ priced: this.priced, readById: this.readById }, { priced, readById });
  }

  async expectValueRange(): Promise<void> {
    const valor = this.page.getByTestId('cotizacion-valor');
    assert.equal(await valor.getAttribute('aria-invalid'), 'true');
    assert.equal(
      await this.page.getByTestId('cotizacion-valor-error').innerText(),
      'El valor asegurado debe estar entre $200.000 y $8.000.000 COP.',
    );
  }

  async expectCalculateDisabled(): Promise<void> {
    assert.equal(await this.page.getByTestId('cotizacion-calcular').isDisabled(), true);
  }

  async expectNoOffer(): Promise<void> {
    await this.page.getByTestId('cotizacion-sin-oferta').waitFor({ state: 'visible' });
    assert.equal(await this.page.getByTestId('cotizacion-oferta').count(), 0);
    assert.equal(new URL(this.page.url()).pathname, '/cms/cotizaciones/nueva');
  }

  async expectClientKept(): Promise<void> {
    assert.equal(await this.page.getByTestId('cotizacion-nombre').inputValue(), CLIENTE);
  }
}
