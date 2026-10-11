import { Page } from 'playwright';

export class ShellPage {
  constructor(private readonly page: Page) {}

  private userShell() {
    return this.page.getByTestId('user-shell');
  }

  async open(): Promise<void> {
    const baseUrl = process.env['BASE_URL'] ?? 'http://localhost:8080';
    await this.page.goto(baseUrl);
  }

  async expectUserShell(): Promise<void> {
    await this.userShell().waitFor({ state: 'visible' });
  }
}
