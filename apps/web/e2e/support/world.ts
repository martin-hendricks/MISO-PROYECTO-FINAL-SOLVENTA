import { IWorldOptions, setWorldConstructor, World } from '@cucumber/cucumber';
import { Browser, chromium, Page } from 'playwright';
import { BackofficePage } from '../pages/backoffice.page';
import { CotizacionPage } from '../pages/cotizacion.page';
import { ConsentimientoPage } from '../pages/consentimiento.page';
import { LoginPage } from '../pages/login.page';
import { InicioPage } from '../pages/inicio.page';
import { PolizaDetallePage } from '../pages/poliza-detalle.page';
import { RegistroPage } from '../pages/registro.page';
import { ShellPage } from '../pages/shell.page';
import { Client, credentials, Credentials, Home, Offer, SignUp } from './data/generators';
import { BffDoubles } from './doubles/bff';

export class PortalWorld extends World {
  private browser!: Browser;
  page!: Page;
  bff!: BffDoubles;
  shell!: ShellPage;
  login!: LoginPage;
  registro!: RegistroPage;
  consentimiento!: ConsentimientoPage;
  backoffice!: BackofficePage;
  inicio!: InicioPage;
  cotizacion!: CotizacionPage;
  polizaDetalle!: PolizaDetallePage;
  account!: Credentials;
  alta!: SignUp;
  clientes: Client[] = [];
  home!: Home;
  offer!: Offer;

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
    this.consentimiento = new ConsentimientoPage(this.page);
    this.backoffice = new BackofficePage(this.page);
    this.inicio = new InicioPage(this.page);
    this.cotizacion = new CotizacionPage(this.page);
    this.polizaDetalle = new PolizaDetallePage(this.page);
    this.account = credentials();
  }

  /** Figma canvas widths referenced by HU-107/SOLV-231 (desktop TopNav vs. the
   * 390 hamburger menu) -- height is a fixed viewport default, only the width
   * drives which nav the CSS media query (max-width: 600px) renders. */
  async setCanvasWidth(width: 1440 | 390): Promise<void> {
    await this.page.setViewportSize({ width, height: 900 });
  }

  async closeBrowser(): Promise<void> {
    await this.browser?.close();
  }
}

setWorldConstructor(PortalWorld);
