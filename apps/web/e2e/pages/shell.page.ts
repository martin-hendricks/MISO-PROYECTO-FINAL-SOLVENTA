import { Page } from 'playwright';

export class ShellPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/');
  }

  async expectInicio(): Promise<void> {
    await this.page.getByTestId('inicio').waitFor({ state: 'visible' });
  }
}
