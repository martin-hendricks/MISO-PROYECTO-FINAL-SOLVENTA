import { Page } from 'playwright';

export class ShellPage {
  constructor(private readonly page: Page) {}

  private userShell() {
    return this.page.getByTestId('user-shell');
  }

  private cmsShell() {
    return this.page.getByTestId('cms-shell');
  }

  private cmsNav() {
    return this.page.getByTestId('nav-cms');
  }

  async open(): Promise<void> {
    const baseUrl = process.env['BASE_URL'] ?? 'http://localhost:8080';
    await this.page.goto(baseUrl);
  }

  async expectUserShell(): Promise<void> {
    await this.userShell().waitFor({ state: 'visible' });
  }

  async openCms(): Promise<void> {
    await this.cmsNav().click();
    await this.page.waitForURL('**/cms');
  }

  async expectCmsShell(): Promise<void> {
    await this.cmsShell().waitFor({ state: 'visible' });
  }
}
