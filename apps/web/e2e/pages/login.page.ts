import assert from 'node:assert/strict';
import { Page } from 'playwright';
import { Credentials } from '../support/data/generators';

export type LoginVariant = 'customer' | 'backoffice';

const PATHS: Record<LoginVariant, string> = {
  customer: '/login',
  backoffice: '/cms/login',
};

export class LoginPage {
  constructor(private readonly page: Page) {}

  private form() {
    return this.page.getByTestId('login-form');
  }

  async open(variant: LoginVariant): Promise<void> {
    await this.page.goto(PATHS[variant]);
  }

  async signIn({ email, password }: Credentials): Promise<void> {
    await this.page.getByTestId('login-email').fill(email);
    await this.page.getByTestId('login-password').fill(password);
    await this.page.getByTestId('login-submit').click();
  }

  async expectVisible(variant: LoginVariant): Promise<void> {
    await this.form().waitFor({ state: 'visible' });
    assert.equal(new URL(this.page.url()).pathname, PATHS[variant]);
  }

  async expectError(kind: 'credentials' | 'network'): Promise<void> {
    await this.page
      .locator(`[data-testid="login-error"][data-kind="${kind}"]`)
      .waitFor({ state: 'visible' });
  }
}
