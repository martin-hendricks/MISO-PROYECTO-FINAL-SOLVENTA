import { Page } from 'playwright';

export class ShellPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/');
  }

  async expectUserShell(): Promise<void> {
    await this.page.getByTestId('user-shell').waitFor({ state: 'visible' });
  }
}
