import { IWorldOptions, setWorldConstructor, World } from '@cucumber/cucumber';
import { Browser, chromium, Page } from 'playwright';
import { LoginPage } from '../pages/login.page';
import { ShellPage } from '../pages/shell.page';

export class PortalWorld extends World {
  private browser!: Browser;
  page!: Page;
  shell!: ShellPage;
  login!: LoginPage;

  constructor(options: IWorldOptions) {
    super(options);
  }

  async openBrowser(): Promise<void> {
    this.browser = await chromium.launch({ headless: true });
    this.page = await this.browser.newPage();
    this.shell = new ShellPage(this.page);
    this.login = new LoginPage(this.page);
  }

  async closeBrowser(): Promise<void> {
    await this.browser?.close();
  }
}

setWorldConstructor(PortalWorld);
