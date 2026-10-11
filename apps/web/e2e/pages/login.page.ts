import assert from 'node:assert/strict';
import { Page } from 'playwright';

const INGRESO = '**/web/sesion/ingreso';

export function tokenPair(rol: 'cliente' | 'asesor' | 'operador' = 'cliente') {
  const claims = {
    sub: 'camila@correo.com',
    rol,
    typ: 'access',
    exp: Math.floor(Date.now() / 1000) + 900,
  };
  const payload = Buffer.from(JSON.stringify(claims)).toString('base64url');
  return { accessToken: `header.${payload}.signature`, refreshToken: 'refresh', expiraEn: 900 };
}

export class LoginPage {
  constructor(private readonly page: Page) {}

  private form() {
    return this.page.getByTestId('login-form');
  }

  async open(): Promise<void> {
    const baseUrl = process.env['BASE_URL'] ?? 'http://localhost:8080';
    await this.page.goto(`${baseUrl}/login`);
    await this.expectVisible();
  }

  async acceptCredentials(): Promise<void> {
    await this.page.route(INGRESO, (route) => route.fulfill({ json: tokenPair() }));
  }

  async rejectCredentials(): Promise<void> {
    await this.page.route(INGRESO, (route) =>
      route.fulfill({ status: 401, json: { detail: 'Credenciales invalidas' } }),
    );
  }

  async dropConnection(): Promise<void> {
    await this.page.route(INGRESO, (route) => route.abort('connectionfailed'));
  }

  async signIn(): Promise<void> {
    await this.page.getByTestId('login-email').fill('camila@correo.com');
    await this.page.getByTestId('login-password').fill('secreto');
    await this.page.getByTestId('login-submit').click();
  }

  async expectVisible(): Promise<void> {
    await this.form().waitFor({ state: 'visible' });
  }

  async expectError(kind: 'credentials' | 'network'): Promise<void> {
    await this.page
      .locator(`[data-testid="login-error"][data-kind="${kind}"]`)
      .waitFor({ state: 'visible' });
  }

  async expectStillOnLogin(): Promise<void> {
    await this.expectVisible();
    assert.equal(new URL(this.page.url()).pathname, '/login');
  }
}
