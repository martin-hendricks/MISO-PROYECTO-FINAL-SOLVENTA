import { Page } from 'playwright';
import { Catalog, Client, Home, Offer, OperatorPolicy, PolicyDetail } from '../data/generators';

export type Role = 'cliente' | 'asesor' | 'operador';

const INGRESO = '**/web/sesion/ingreso';
const SALIDA = '**/web/sesion/salida';
const CLIENTES = '**/web/asesor/clientes';
const ASESOR_COTIZACIONES = '**/web/asesor/cotizaciones?**';
const INICIO = '**/web/cliente/inicio';
const POLIZAS_LISTA = '**/web/cliente/polizas';
const POLIZA_DETALLE = '**/web/cliente/polizas/*';
const COTIZACIONES = '**/web/cliente/cotizaciones**';
const REGISTRO = '**/web/registro';
const ASESOR_EMISION = '**/web/asesor/emisiones';
const ASESOR_POLIZA = '**/web/asesor/emisiones/*/poliza';
const OPERADOR_POLIZA_DETALLE = '**/web/operador/polizas/*';
const OPERADOR_POLIZA_CICLO = '**/web/operador/polizas/ciclo';

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

export type Canal = 'cliente' | 'asesor';

export class BffDoubles {
  private clientsServed = false;
  private quoteRequests = 0;
  private quoteBodies: Record<string, unknown>[] = [];
  private offerReads = 0;
  private issueRequests = 0;
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
    await this.servePendingQuotes();
  }

  /** Answers the advisor's pending quotes (HU-163) with an empty first page. */
  async servePendingQuotes(): Promise<void> {
    await this.page.unroute(ASESOR_COTIZACIONES);
    await this.page.route(ASESOR_COTIZACIONES, (route) =>
      route.fulfill({
        json: { items: [], pagina: 1, tamano: 20, hayMas: false, avisos: [] },
      }),
    );
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

  async servePolicyDetail(detail: PolicyDetail): Promise<void> {
    await this.page.unroute(POLIZA_DETALLE);
    await this.page.route(POLIZA_DETALLE, (route) => route.fulfill({ json: detail }));
  }

  async servePolicyList(policies: PolicyDetail[]): Promise<void> {
    await this.page.unroute(POLIZAS_LISTA);
    await this.page.route(POLIZAS_LISTA, (route) => route.fulfill({ json: { polizas: policies } }));
  }

  /** Single handler for both GET .../polizas/{numero} and POST .../ciclo:
   * Playwright matches overlapping glob routes in reverse registration
   * order, and `**\/polizas/*` also matches `.../polizas/ciclo`, so two
   * separate `page.route()` calls race each other for the same POST. One
   * handler per URL pattern, dispatching on method, avoids that entirely. */
  private async serveOperatorPolicyWith(
    detalle: (policy: OperatorPolicy) => OperatorPolicy,
    ciclo: (
      policy: OperatorPolicy,
      body: { verbo: string; motivo?: string },
    ) => { status?: number; json: unknown },
    policy: OperatorPolicy,
  ): Promise<void> {
    let current = policy;
    await this.page.unroute(OPERADOR_POLIZA_CICLO);
    await this.page.unroute(OPERADOR_POLIZA_DETALLE);
    await this.page.route(OPERADOR_POLIZA_DETALLE, (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON() as { verbo: string; motivo?: string };
        const { status, json } = ciclo(current, body);
        if (json && typeof json === 'object' && 'numero' in json) {
          current = json as OperatorPolicy;
        }
        return route.fulfill({ status, json });
      }
      current = detalle(current);
      return route.fulfill({ json: current });
    });
  }

  /** Answers the operator's policy screen (HU-59/61) with a single stateful
   * double, same shape as the real core (renovar keeps renovable true
   * unless told otherwise, cancelar answers with the cancellation record). */
  async serveOperatorPolicy(policy: OperatorPolicy): Promise<void> {
    await this.serveOperatorPolicyWith(
      (current) => current,
      (current, body) => {
        if (body.verbo === 'renovar') {
          return { json: { ...current, venceEn: '2028-10-01' } };
        }
        if (body.verbo === 'cancelar') {
          return {
            json: {
              ...current,
              estado: 'cancelada',
              renovable: false,
              devolucionEstimada: 500,
              canceladaEn: '2026-11-01',
              canceladaPor: 'persona@solventa.com',
              motivoCancelacion: body.motivo ?? '',
            },
          };
        }
        return { json: current };
      },
      policy,
    );
  }

  /** Same double as `serveOperatorPolicy`, but cancelar always answers 409
   * (ya cancelada) regardless of the body -- for "already cancelled". */
  async serveOperatorPolicyAlreadyCancelled(policy: OperatorPolicy): Promise<void> {
    const cancelled: OperatorPolicy = {
      ...policy,
      estado: 'cancelada',
      renovable: false,
      devolucionEstimada: 500,
      canceladaEn: '2026-11-01',
      canceladaPor: 'persona@solventa.com',
      motivoCancelacion: 'El cliente lo pidió',
    };
    await this.serveOperatorPolicyWith(
      () => cancelled,
      () => ({
        status: 409,
        json: { codigo: 'transicion_invalida', mensaje: 'La póliza ya estaba cancelada' },
      }),
      cancelled,
    );
  }

  /** Same shape, but renovar always answers 409 (vencida fuera de la ventana
   * de gracia) -- for "policy no longer valid". */
  async serveOperatorPolicyNotRenewable(policy: OperatorPolicy): Promise<void> {
    const notRenewable: OperatorPolicy = { ...policy, renovable: false };
    await this.serveOperatorPolicyWith(
      () => notRenewable,
      () => ({
        status: 409,
        json: { codigo: 'transicion_invalida', mensaje: 'No se puede pasar de VIGENTE a VIGENTE' },
      }),
      notRenewable,
    );
  }

  /** Counts every call to the quote endpoints. Accepting an offer must not make one. */
  async watchQuotes(): Promise<void> {
    await this.page.route(COTIZACIONES, (route) => {
      this.quoteRequests += 1;
      return route.fulfill({ status: 500, json: { detail: 'No se esperaba una cotización' } });
    });
  }

  /** Answers `GET /{canal}/catalogo/{ramo}` with the catalog of the requested line. */
  async serveCatalogs(canal: Canal, catalogs: Record<string, Catalog>): Promise<void> {
    await this.page.route(`**/web/${canal}/catalogo/*`, (route) => {
      const ramo = decodeURIComponent(new URL(route.request().url()).pathname.split('/').pop()!);
      const catalog = catalogs[ramo];
      return catalog
        ? route.fulfill({ json: catalog })
        : route.fulfill({ status: 404, json: { codigo: 'no_encontrado', mensaje: 'No existe' } });
    });
  }

  /** Quotes once with `offer` and reconsults it by id without recalculating (HU-7). */
  async serveQuote(canal: Canal, offer: Offer): Promise<void> {
    await this.page.route(`**/web/${canal}/cotizaciones`, (route) => {
      this.quoteRequests += 1;
      this.quoteBodies.push(route.request().postDataJSON() as Record<string, unknown>);
      return route.fulfill({ json: offer });
    });
    await this.page.route(`**/web/cliente/cotizaciones/${offer.cotizacionId}`, (route) => {
      this.offerReads += 1;
      return route.fulfill({ json: offer });
    });
  }

  /** Answers the advisor issuance (HU-149): the core decision, then the sign-and-issue result. */
  async serveAdvisorIssuance(
    decision: Record<string, unknown>,
    emision: Record<string, unknown>,
  ): Promise<void> {
    await this.page.route(ASESOR_EMISION, (route) => route.fulfill({ json: decision }));
    await this.page.route(ASESOR_POLIZA, (route) => {
      this.issueRequests += 1;
      return route.fulfill({ json: emision });
    });
  }

  issuesRequested(): number {
    return this.issueRequests;
  }

  quoteBody(): Record<string, unknown> | undefined {
    return this.quoteBodies.at(-1);
  }

  offersRead(): number {
    return this.offerReads;
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
