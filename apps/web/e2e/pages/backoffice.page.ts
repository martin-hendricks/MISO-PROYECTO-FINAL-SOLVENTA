import assert from 'node:assert/strict';
import { Page } from 'playwright';
import { tokenPair } from './login.page';

type StaffRole = 'asesor' | 'operador';
type Section = 'clientes' | 'cotizaciones' | 'polizas' | 'avisos';

const CLIENTES = [
  ['CLI-18', 'Andrés Gómez', 'web', 'activo', 'habeas_data'],
  ['CLI-19', 'Laura Peña', 'android', 'activo', 'habeas_data'],
  ['CLI-20', 'Ricardo Salas', 'web', 'activo', 'hipotecario_pendiente'],
  ['CLI-21', 'Marcela Ruiz', 'android', 'activo', 'habeas_data'],
  ['CLI-22', 'Julián Torres', 'web', 'inactivo', 'revocado'],
].map(([clienteId, nombre, canal, estado, consentimiento]) => ({
  clienteId,
  nombre,
  documento: '1020334556',
  canal,
  estado,
  consentimiento,
}));

export class BackofficePage {
  constructor(private readonly page: Page) {}

  private baseUrl(): string {
    return process.env['BASE_URL'] ?? 'http://localhost:8080';
  }

  private section(name: Section) {
    return this.page.getByTestId(`section-${name}`);
  }

  async open(): Promise<void> {
    await this.page.goto(`${this.baseUrl()}/cms`);
  }

  async signInAs(role: StaffRole): Promise<void> {
    await this.page.route('**/web/sesion/ingreso', (route) =>
      route.fulfill({ json: tokenPair(role) }),
    );
    await this.page.route('**/web/sesion/salida', (route) =>
      route.fulfill({ json: { estado: 'aceptada' } }),
    );
    await this.page.route('**/web/asesor/clientes', (route) =>
      route.fulfill({ json: { clientes: CLIENTES } }),
    );
    await this.page.goto(`${this.baseUrl()}/cms/login`);
    await this.page.getByTestId('login-email').fill(`${role}@solventa.co`);
    await this.page.getByTestId('login-password').fill('secreto');
    await this.page.getByTestId('login-submit').click();
    await this.page.getByTestId('top-nav-admin').waitFor({ state: 'visible' });
  }

  async openSection(name: Section): Promise<void> {
    await this.page.getByTestId(`nav-${name}`).click();
    await this.section(name).waitFor({ state: 'visible' });
  }

  async signOut(): Promise<void> {
    await this.page.getByTestId('sign-out').click();
  }

  async expectLogin(): Promise<void> {
    await this.page.getByTestId('login-form').waitFor({ state: 'visible' });
    assert.equal(new URL(this.page.url()).pathname, '/cms/login');
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

  async expectClients(count: number): Promise<void> {
    await this.page.getByTestId('clientes-table').waitFor({ state: 'visible' });
    assert.equal(await this.page.locator('[data-testid="clientes-table"] tbody tr').count(), count);
  }

  async expectNoPermission(current: StaffRole, required: StaffRole): Promise<void> {
    const state = this.page.getByTestId('no-permission');
    await state.waitFor({ state: 'visible' });
    assert.equal(await state.getAttribute('data-current'), current);
    assert.equal(await state.getAttribute('data-required'), required);
  }
}
