import { Page } from 'playwright';
import {
  Catalog,
  Client,
  Home,
  MortgageOffer,
  Offer,
  OperatorPolicy,
  PolicyDetail,
  PolicyNotice,
} from '../data/generators';

export type Role = 'cliente' | 'asesor' | 'operador';

const INGRESO = '**/web/sesion/ingreso';
const SALIDA = '**/web/sesion/salida';
const CLIENTES = '**/web/operador/clientes**';
const NOTIFICACIONES = '**/web/operador/notificaciones/**';
const ASESOR_COTIZACIONES = '**/web/asesor/cotizaciones?**';
const INICIO = '**/web/cliente/inicio';
const PERFIL = '**/web/cliente/perfil';
const POLIZAS_LISTA = '**/web/cliente/polizas';
const POLIZA_DETALLE = '**/web/cliente/polizas/*';
// Más específica que POLIZA_DETALLE (que también matchea esta URL, ver el
// comentario de serveOperatorPolicyWith sobre el orden de registro inverso de
// Playwright) -- se registra DESPUÉS de servePolicyDetail en cualquier step
// que necesite ambas, para que esta gane primero.
const POLIZAS_AVISOS = '**/web/cliente/polizas/por-vencer';
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
  private mortgageBodies: Record<string, unknown>[] = [];
  private originationBodies: Record<string, unknown>[] = [];

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

  /** Profile is read when Perfil opens. A live 401 would sign the customer out. */
  async serveProfile(correo: string): Promise<void> {
    await this.page.route(PERFIL, (route) =>
      route.fulfill({
        json: {
          usuarioId: 'usuario-e2e',
          correo,
          nombre: 'Camila',
          apellidos: 'Restrepo',
          documento: '1012345678',
        },
      }),
    );
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
    await this.replaceClients((route) =>
      route.fulfill({
        json: {
          clientes: clientes.map((cliente) => ({
            usuarioId: cliente.clienteId,
            nombre: cliente.nombre,
            apellidos: '',
            email: `${cliente.clienteId.toLowerCase()}@correo.com`,
            documento: cliente.documento,
            estado: cliente.estado === 'inactivo' ? 'INACTIVO' : 'ACTIVO',
            dispositivosActivos: cliente.estado === 'inactivo' ? 0 : 1,
          })),
          pagina: 1,
          hayMas: false,
        },
      }),
    );
    await this.servePendingQuotes();
  }

  async serveDirectory(
    clientes: {
      usuarioId: string;
      nombre: string;
      apellidos: string;
      email: string;
      documento: string;
      estado: 'ACTIVO' | 'INACTIVO';
      dispositivosActivos: number | null;
    }[],
  ): Promise<void> {
    await this.replaceClients((route) =>
      route.fulfill({ json: { clientes, pagina: 1, hayMas: false } }),
    );
    await this.servePendingQuotes();
  }

  async serveBroadcast(audiencia: {
    usuarioId: string;
    nombre: string;
    apellidos: string;
    email: string;
    documento: string;
    dispositivosActivos: number;
  }[]): Promise<void> {
    const historial: {
      difusionId: string;
      titulo: string;
      cuerpo: string;
      poliza: string | null;
      creadaEn: string;
      enviadas: number;
      fallidas: number;
      sinDispositivo: number;
    }[] = [];
    await this.page.unroute(NOTIFICACIONES);
    await this.page.route(NOTIFICACIONES, (route) => {
      const path = new URL(route.request().url()).pathname;
      if (path.endsWith('/audiencia')) {
        return route.fulfill({ json: { usuarios: audiencia } });
      }
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON() as { titulo: string; cuerpo: string; poliza?: string };
        const item = {
          difusionId: 'c2d40000-0000-4000-8000-000000000001',
          titulo: body.titulo,
          cuerpo: body.cuerpo,
          poliza: body.poliza ?? null,
          creadaEn: '2026-11-09T13:05:00Z',
          enviadas: 2,
          fallidas: 0,
          sinDispositivo: 0,
        };
        historial.unshift(item);
        return route.fulfill({ status: 201, json: item });
      }
      return route.fulfill({ json: { items: historial } });
    });
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

  /** HU-119: pólizas vigentes del cliente que vencen pronto. Registrar
   * después de servePolicyDetail si el escenario también necesita esa ruta. */
  async serveNotices(notices: PolicyNotice[]): Promise<void> {
    await this.page.unroute(POLIZAS_AVISOS);
    await this.page.route(POLIZAS_AVISOS, (route) => route.fulfill({ json: { polizas: notices } }));
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
      body: { verbo: string; motivo?: string; coberturas?: OperatorPolicy['coberturas'] },
    ) => { status?: number; json: unknown },
    policy: OperatorPolicy,
  ): Promise<void> {
    let current = policy;
    await this.page.unroute(OPERADOR_POLIZA_CICLO);
    await this.page.unroute(OPERADOR_POLIZA_DETALLE);
    await this.page.route(OPERADOR_POLIZA_DETALLE, (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON() as {
          verbo: string;
          motivo?: string;
          coberturas?: OperatorPolicy['coberturas'];
        };
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
        if (body.verbo === 'modificar') {
          return { json: { ...current, coberturas: body.coberturas ?? current.coberturas } };
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

  /** Keeps customer issuance inside the portal. A live BFF 401 would sign the customer out. */
  async serveCustomerIssuance(): Promise<void> {
    await this.page.route(POLIZAS_LISTA, (route) => {
      if (route.request().method() !== 'POST') {
        return route.fallback();
      }
      return route.fulfill({
        json: {
          resultado: 'EMITIDA',
          poliza: {
            numero: 'POL-2026-00088421',
            producto: 'Protección de dispositivo',
            estado: 'VIGENTE',
            inicioVigencia: '2026-03-12',
            finVigencia: '2027-03-12',
            moneda: 'COP',
            primaTotal: 42300,
          },
        },
      });
    });
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

  /** Answers the customer issuance `POST /cliente/polizas` with a core refusal (HU-165). */
  async refuseIssuance(status: number, body: Record<string, unknown>): Promise<void> {
    await this.page.route(POLIZAS_LISTA, (route) => {
      if (route.request().method() !== 'POST') return route.fallback();
      this.issueRequests += 1;
      return route.fulfill({ status, json: body });
    });
  }

  /** Answers the customer mortgage origination: GET returns the pending one (or 404), POST saves it. */
  async serveMortgageOrigination(pending: { valor: number; plazoMeses: number } | null): Promise<void> {
    const url = '**/web/cliente/originacion-hipotecaria';
    await this.page.unroute(url);
    await this.page.route(url, (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON() as Record<string, unknown>;
        this.originationBodies.push(body);
        return route.fulfill({ status: 201, json: { ...body, origen: 'cliente' } });
      }
      return pending
        ? route.fulfill({ json: { ...pending, origen: 'cliente' } })
        : route.fulfill({ status: 404, json: { codigo: 'no_encontrado', mensaje: 'No existe' } });
    });
  }

  originationBody(): Record<string, unknown> | undefined {
    return this.originationBodies.at(-1);
  }

  /** Answers `POST /{canal}/oferta-hipotecaria` (HU-162); a new call replaces the answer. */
  async serveMortgageOffer(canal: Canal, offer: MortgageOffer): Promise<void> {
    const url = `**/web/${canal}/oferta-hipotecaria`;
    await this.page.unroute(url);
    await this.page.route(url, (route) => {
      this.mortgageBodies.push(route.request().postDataJSON() as Record<string, unknown>);
      return route.fulfill({ json: offer });
    });
  }

  mortgageBody(): Record<string, unknown> | undefined {
    return this.mortgageBodies.at(-1);
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
