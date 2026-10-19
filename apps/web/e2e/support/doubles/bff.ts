import { Page } from 'playwright';
import { Client } from '../data/generators';

export type Role = 'cliente' | 'asesor' | 'operador';

const INGRESO = '**/web/sesion/ingreso';
const SALIDA = '**/web/sesion/salida';
const CLIENTES = '**/web/asesor/clientes';

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

  constructor(private readonly page: Page) {}

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

  hasClients(): boolean {
    return this.clientsServed;
  }

  private async replaceClients(handler: Parameters<Page['route']>[1]): Promise<void> {
    await this.page.unroute(CLIENTES);
    await this.page.route(CLIENTES, handler);
    this.clientsServed = true;
  }
}
