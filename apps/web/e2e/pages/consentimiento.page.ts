import { Page } from 'playwright';

export class ConsentimientoPage {
  constructor(private readonly page: Page) {}

  async grant(): Promise<void> {
    await this.page.getByTestId('consentimiento-accept').check();
    await this.page.getByTestId('consentimiento-submit').click();
  }
}
