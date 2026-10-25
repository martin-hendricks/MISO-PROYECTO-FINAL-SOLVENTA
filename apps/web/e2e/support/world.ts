import { IWorldOptions, setWorldConstructor, World } from '@cucumber/cucumber';
import { Browser, chromium, Page } from 'playwright';
import { BackofficePage } from '../pages/backoffice.page';
import { LoginPage } from '../pages/login.page';
import { InicioPage } from '../pages/inicio.page';
import { RegistroPage } from '../pages/registro.page';
import { ShellPage } from '../pages/shell.page';
import { Client, credentials, Credentials, Home } from './data/generators';
import { BffDoubles } from './doubles/bff';

export class PortalWorld extends World {
  private browser!: Browser;
  page!: Page;
  bff!: BffDoubles;
  shell!: ShellPage;
  login!: LoginPage;
  registro!: RegistroPage;
  backoffice!: BackofficePage;
  inicio!: InicioPage;
  account!: Credentials;
  clientes: Client[] = [];
  home!: Home;

  constructor(options: IWorldOptions) {
    super(options);
  }

  async openBrowser(): Promise<void> {
    this.browser = await chromium.launch({ headless: true });
    const context = await this.browser.newContext({
      baseURL: process.env['BASE_URL'] ?? 'http://localhost:8080',
    });
    this.page = await context.newPage();
    this.bff = new BffDoubles(this.page);
    this.shell = new ShellPage(this.page);
    this.login = new LoginPage(this.page);
    this.registro = new RegistroPage(this.page);
    this.backoffice = new BackofficePage(this.page);
    this.inicio = new InicioPage(this.page);
    this.account = credentials();
  }

  async closeBrowser(): Promise<void> {
    await this.browser?.close();
  }
}

setWorldConstructor(PortalWorld);
