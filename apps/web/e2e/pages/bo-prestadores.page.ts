import assert from 'node:assert/strict';
import { Page } from 'playwright';

export class BoPrestadoresPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/cms/prestadores');
    await this.page.getByTestId('section-prestadores').waitFor({ state: 'visible' });
  }

  async expectCounts(texto: RegExp): Promise<void> {
    const conteos = this.page.getByTestId('prestadores-conteos');
    await conteos.waitFor({ state: 'visible' });
    assert.match((await conteos.textContent()) ?? '', texto);
  }

  async filterCountry(pais: string): Promise<void> {
    await this.page.getByTestId('filtro-pais').selectOption(pais);
  }

  async expectFilterCities(ciudades: string[]): Promise<void> {
    await this.expectOptions('filtro-ciudad', ciudades);
  }

  async openNew(): Promise<void> {
    await this.page.getByTestId('prestadores-nuevo').click();
    await this.page.getByTestId('prestador-nombre').waitFor({ state: 'visible' });
  }

  async pickFormCountry(pais: string): Promise<void> {
    await this.page.getByTestId('prestador-pais').selectOption(pais);
  }

  async expectFormCities(ciudades: string[]): Promise<void> {
    await this.expectOptions('prestador-ciudad', ciudades);
  }

  async expectNoRow(id: string): Promise<void> {
    assert.equal(await this.page.getByTestId(`bo-prestador-${id}`).count(), 0);
  }

  /** Options with a value, in order, once the first expected city has arrived. */
  private async expectOptions(testId: string, ciudades: string[]): Promise<void> {
    const select = this.page.getByTestId(testId);
    await select.locator(`option[value="${ciudades[0]}"]`).waitFor({ state: 'attached' });
    const valores = await select
      .locator('option')
      .evaluateAll((opciones) =>
        opciones.map((opcion) => (opcion as HTMLOptionElement).value).filter(Boolean),
      );
    assert.deepEqual(valores, ciudades);
  }

  async expectRow(id: string): Promise<void> {
    await this.page.getByTestId(`bo-prestador-${id}`).waitFor({ state: 'visible' });
  }

  async expectNoCreateOrDeactivate(): Promise<void> {
    assert.equal(await this.page.getByTestId('prestadores-nuevo').count(), 0);
    assert.equal(await this.page.getByTestId(/^inactivar-/).count(), 0);
  }

  async create(nombre: string): Promise<void> {
    await this.page.getByTestId('prestadores-nuevo').click();
    await this.page.getByTestId('prestador-nombre').waitFor({ state: 'visible' });
    await this.page.getByTestId('prestador-nombre').fill(nombre);
    await this.page.getByTestId('prestador-barrio').fill('Usaquén');
    await this.page.getByTestId('prestador-tipo').selectOption('taller-motos');
    await this.page.getByTestId('prestador-telefono').fill('601 555 0199');
    await this.page.getByTestId('prestador-direccion').fill('Cra 7 #120-10');
    await this.page.getByTestId('prestador-horario').fill('Lun–Vie 8:00–18:00');
    await this.page.getByTestId('prestador-ciudad').selectOption('Bogotá');
    await this.page.getByTestId('chip-ramo-soat-motocicleta').click();
    await this.page.getByTestId('prestador-lat').fill('4.7');
    await this.page.getByTestId('prestador-lng').fill('-74.03');
    await this.page.getByTestId('prestador-guardar').click();
    await this.page.getByTestId('section-prestadores').waitFor({ state: 'visible' });
  }

  async expectName(nombre: string): Promise<void> {
    await this.page.getByTestId('bo-prestador-PRE-E2E-01').waitFor({ state: 'visible' });
    assert.match(
      (await this.page.getByTestId('bo-prestador-PRE-E2E-01').textContent()) ?? '',
      new RegExp(nombre),
    );
  }

  async editName(nombre: string): Promise<void> {
    await this.page.getByTestId('editar-PRE-E2E-01').click();
    await this.page.getByTestId('prestador-nombre').waitFor({ state: 'visible' });
    await this.page.getByTestId('prestador-nombre').fill(nombre);
    await this.page.getByTestId('prestador-guardar').click();
    await this.page.getByTestId('section-prestadores').waitFor({ state: 'visible' });
  }

  async deactivate(id: string): Promise<void> {
    await this.page.getByTestId(`inactivar-${id}`).click();
    await this.page.getByTestId('confirm-dialog').waitFor({ state: 'visible' });
    await this.page.getByTestId('confirm-dialog-confirmar').click();
  }

  async reactivate(id: string): Promise<void> {
    await this.page.getByTestId(`inactivar-${id}`).waitFor({ state: 'hidden' });
    await this.page.getByTestId(`reactivar-${id}`).click();
    await this.page.getByTestId(`inactivar-${id}`).waitFor({ state: 'visible' });
  }

  async filterEmpty(): Promise<void> {
    await this.page.getByTestId('filtro-ciudad').selectOption('Chía');
    await this.page.getByTestId('filtro-ramo').selectOption('clima-y-vuelos');
    await this.page.getByTestId('prestadores-vacio').waitFor({ state: 'visible' });
  }

  async expectEmpty(): Promise<void> {
    await this.page.getByTestId('prestadores-vacio').waitFor({ state: 'visible' });
    await this.page.getByTestId('prestadores-vacio-detalle').waitFor({ state: 'visible' });
  }

  async clearFilters(): Promise<void> {
    await this.page.getByTestId('prestadores-quitar-filtros').click();
    await this.page.getByTestId('prestadores-table').waitFor({ state: 'visible' });
  }
}
