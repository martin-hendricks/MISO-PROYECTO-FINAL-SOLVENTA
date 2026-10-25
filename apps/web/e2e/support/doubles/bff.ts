import { Page } from 'playwright';
import { Client, Home } from '../data/generators';

export type Role = 'cliente' | 'asesor' | 'operador';

const INGRESO = '**/web/sesion/ingreso';
const SALIDA = '**/web/sesion/salida';
const CLIENTES = '**/web/asesor/clientes';
const INICIO = '**/web/cliente/inicio';
const COTIZACIONES = '**/web/cliente/cotizaciones**';
const REGISTRO = '**/web/registro';

export interface ConsentMark {
  habeasData: boolean;
  otorgadoEn: string;
  version: string;
}

export function tokenPair(subject: string, rol: Role) {
  const claims = {
    sub: subject,
    rol,
    typ: 'access',
    exp: Math.floor(Date.now() / 1000) + 900,
  };
  const payload = Buffer.from(JSON.stringify(claims)).toString('base64url');
  return { accessToken: `header.${payload}.signature`, refreshToken: 'refresh', expiraEn: 900 };
}

export class BffDoubles {
  private clientsServed = false;
  private quoteRequests = 0;
  private signUpBody: Record<string, unknown> | null = null;
  private consentMark: ConsentMark | null = null;

  constructor(private readonly page: Page) {}

  /** Answers the sign-up as `bff-web` does: a customer session plus the consent mark. */
  async acceptSignUp(): Promise<void> {
    await this.page.route(REGISTRO, (route) => {
      const body = route.request().postDataJSON() as Record<string, unknown>;
      const correo = String(body['correo']);
      this.signUpBody = body;
      this.consentMark = {
        habeasData: true,
        otorgadoEn: new Date().toISOString(),
        version: '2026-10',
      };
      return route.fulfill({
        json: {
          ...tokenPair(correo, 'cliente'),
          cliente: {
            nombre: body['nombre'],
            apellidos: body['apellidos'],
            documento: body['documento'],
            correo,
          },
          consentimiento: this.consentMark,
        },
      });
    });
  }

  signUpRequest(): Record<string, unknown> | null {
    return this.signUpBody;
  }

  grantedConsent(): ConsentMark | null {
    return this.consentMark;
  }

  async acceptSignIn(subject: string, rol: Role): Promise<void> {
    await this.page.route(INGRESO, (route) => route.fulfill({ json: tokenPair(subject, rol) }));
    await this.page.route(SALIDA, (route) => route.fulfill({ json: { estado: 'aceptada' } }));
  }

  async rejectSignIn(): Promise<void> {
    await this.page.route(INGRESO, (route) =>
      route.fulfill({ status: 401, json: { detail: 'Credenciales invalidas' } }),
    );
  }

  async dropSignIn(): Promise<void> {
    await this.page.route(INGRESO, (route) => route.abort('connectionfailed'));
  }

  async serveClients(clientes: Client[]): Promise<void> {
    await this.replaceClients((route) => route.fulfill({ json: { clientes } }));
  }

  async failClients(): Promise<void> {
    await this.replaceClients((route) =>
      route.fulfill({ status: 503, json: { detail: 'Servicio no disponible' } }),
    );
  }

  async serveHome(home: Home): Promise<void> {
    await this.page.unroute(INICIO);
    await this.page.route(INICIO, (route) => route.fulfill({ json: home }));
  }

  /** Counts every call to the quote endpoints. Accepting an offer must not make one. */
  async watchQuotes(): Promise<void> {
    await this.page.route(COTIZACIONES, (route) => {
      this.quoteRequests += 1;
      return route.fulfill({ status: 500, json: { detail: 'No se esperaba una cotización' } });
    });
  }

  quotesRequested(): number {
    return this.quoteRequests;
  }

  hasClients(): boolean {
    return this.clientsServed;
  }

  private async replaceClients(handler: Parameters<Page['route']>[1]): Promise<void> {
    await this.page.unroute(CLIENTES);
    await this.page.route(CLIENTES, handler);
    this.clientsServed = true;
  }
}
