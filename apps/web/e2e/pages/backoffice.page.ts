import assert from 'node:assert/strict';
import { Page } from 'playwright';
import { Role } from '../support/doubles/bff';
import { Client } from '../support/data/generators';

export type Section = 'clientes' | 'cotizaciones' | 'polizas' | 'avisos';

export class BackofficePage {
  constructor(private readonly page: Page) {}

  private section(name: Section) {
    return this.page.getByTestId(`section-${name}`);
  }

  async open(): Promise<void> {
    await this.page.goto('/cms');
  }

  async waitForShell(): Promise<void> {
    await this.page.getByTestId('top-nav-admin').waitFor({ state: 'visible' });
  }

  async openSection(name: Section): Promise<void> {
    await this.page.getByTestId(`nav-${name}`).click();
    await this.section(name).waitFor({ state: 'visible' });
  }

  async signOut(): Promise<void> {
    await this.page.getByTestId('sign-out').click();
  }

  async goHomeFromNoPermission(): Promise<void> {
    await this.page.getByTestId('no-permission-home').click();
  }

  async retryClients(): Promise<void> {
    await this.page.getByTestId('clientes-retry').click();
  }

  async expectShell(): Promise<void> {
    await this.page.getByTestId('backoffice-tag').waitFor({ state: 'visible' });
    const destinations = await this.page
      .getByTestId('top-nav-admin')
      .locator('nav a')
      .allInnerTexts();
    assert.deepEqual(
      destinations.map((text) => text.trim()),
      ['Clientes', 'Cotizaciones', 'Pólizas', 'Avisos'],
    );
  }

  async expectCurrentSection(name: Section): Promise<void> {
    await this.section(name).waitFor({ state: 'visible' });
    assert.equal(new URL(this.page.url()).pathname, `/cms/${name}`);
    assert.equal(await this.page.locator('nav a[aria-current="page"]').count(), 1);
    assert.equal(await this.page.getByTestId(`nav-${name}`).getAttribute('aria-current'), 'page');
  }

  async expectClients(clientes: Client[]): Promise<void> {
    await this.page.getByTestId('clientes-table').waitFor({ state: 'visible' });
    assert.equal(
      await this.page.locator('[data-testid="clientes-table"] tbody tr').count(),
      clientes.length,
    );
    for (const cliente of clientes) {
      const row = this.page.getByTestId(`cliente-${cliente.clienteId}`);
      assert.equal((await row.locator('th').innerText()).trim(), cliente.nombre);
      assert.equal((await row.locator('td').first().innerText()).trim(), cliente.documento);
    }
  }

  async expectClientsState(state: 'empty' | 'error'): Promise<void> {
    await this.page.getByTestId(`clientes-${state}`).waitFor({ state: 'visible' });
    assert.equal(await this.page.getByTestId('clientes-table').count(), 0);
  }

  async expectNoPermission(current: Role, required: Role): Promise<void> {
    const state = this.page.getByTestId('no-permission');
    await state.waitFor({ state: 'visible' });
    assert.equal(await state.getAttribute('data-current'), current);
    assert.equal(await state.getAttribute('data-required'), required);
  }
}
