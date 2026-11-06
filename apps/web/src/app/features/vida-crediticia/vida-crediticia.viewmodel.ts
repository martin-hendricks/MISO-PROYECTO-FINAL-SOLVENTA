import { computed, signal } from '@angular/core';
import { forkJoin, interval, Observable, of, Subscription, take, timer } from 'rxjs';
import { Catalogo, RechazoCotizacion, rechazoDe } from '../cotizacion/cotizacion.gateway';
import { Campo, ProblemaCampo, Rango, validarCampo } from '../cotizacion/ramos';
import { Credito, OfertaHipotecaria } from './vida-crediticia.gateway';

export type VidaCrediticiaStatus = 'consent' | 'requesting' | 'offer' | 'rejected' | 'error';
export type CatalogoStatus = 'loading' | 'ready' | 'error';

/** The mortgage data, with the keys of the `vida-hipotecario` catalog that bounds them. */
export const CAMPOS_CREDITO: readonly Campo[] = [
  { clave: 'valor', tipo: 'moneda' },
  { clave: 'plazoMeses', tipo: 'numero' },
];

/** What Solventa does after "Autorizar", in the order the customer sees it. */
export const ETAPAS = ['openFinance', 'openData', 'riesgo', 'oferta'] as const;
export type Etapa = (typeof ETAPAS)[number];
export type EstadoEtapa = 'done' | 'active' | 'pending';

/** Time each step stays on screen, so the customer can follow the profiling. */
export const ETAPA_MS = 700;

/**
 * Mortgage life origination (HU-105): the mortgage data comes from Nueva
 * cotización or a partner, the customer only reviews it and authorizes
 * profiling; "Ahora no" leaves without calling anyone. The offer is a firm
 * quote, so accepting it goes to the regular emission.
 */
export class VidaCrediticiaViewModel {
  private readonly statusState = signal<VidaCrediticiaStatus>('consent');
  readonly status = this.statusState.asReadonly();

  private readonly catalogoState = signal<Catalogo | null>(null);
  private readonly catalogoStatusState = signal<CatalogoStatus>('loading');
  readonly catalogoStatus = this.catalogoStatusState.asReadonly();
  readonly moneda = computed(() => this.catalogoState()?.moneda ?? 'COP');

  readonly rangos = computed(() => {
    const rangos: Record<string, Rango> = {};
    for (const dato of this.catalogoState()?.datosRiesgo ?? []) {
      if (dato.tipo === 'rango') {
        rangos[dato.nombre] = { minimo: dato.minimo, maximo: dato.maximo };
      }
    }
    return rangos;
  });

  private readonly valoresState = signal<Readonly<Record<string, string>>>({});
  private readonly touchedState = signal<ReadonlySet<string>>(new Set());

  private readonly ofertaState = signal<OfertaHipotecaria | null>(null);
  readonly oferta = this.ofertaState.asReadonly();

  private readonly rechazoState = signal<RechazoCotizacion | null>(null);
  readonly rechazo = this.rechazoState.asReadonly();

  private readonly etapaState = signal(0);
  private avance: Subscription | null = null;

  private readonly problems = computed(() => {
    const problems: Record<string, ProblemaCampo | null> = {};
    for (const campo of CAMPOS_CREDITO) {
      problems[campo.clave] = validarCampo(
        campo,
        this.valor(campo.clave),
        this.rangos()[campo.clave],
        [],
      );
    }
    return problems;
  });

  readonly canAuthorize = computed(
    () =>
      this.catalogoStatusState() === 'ready' &&
      this.statusState() !== 'requesting' &&
      Object.values(this.problems()).every((problem) => problem === null),
  );

  constructor(
    private readonly catalogSource: () => Observable<Catalogo>,
    private readonly source: (credito: Credito) => Observable<OfertaHipotecaria>,
    private readonly etapaMs: number = ETAPA_MS,
  ) {}

  loadCatalog(): void {
    this.catalogoStatusState.set('loading');
    this.catalogSource().subscribe({
      next: (catalogo) => {
        this.catalogoState.set(catalogo);
        this.catalogoStatusState.set('ready');
      },
      error: () => this.catalogoStatusState.set('error'),
    });
  }

  /** Fills the mortgage data the customer or the partner already entered. */
  prefill(credito: Credito): void {
    this.valoresState.set({ valor: String(credito.valor), plazoMeses: String(credito.plazoMeses) });
  }

  valor(clave: string): string {
    return this.valoresState()[clave] ?? '';
  }

  numero(clave: string): number {
    return Number(this.valor(clave));
  }

  /** A typed value that is not valid; untouched empty fields show no error yet. */
  issue(clave: string): ProblemaCampo | null {
    const typed = this.valor(clave) !== '';
    return typed || this.touchedState().has(clave) ? this.problems()[clave] : null;
  }

  touch(clave: string): void {
    this.touchedState.update((touched) => new Set(touched).add(clave));
  }

  /** Editing the mortgage data drops a rejection about the previous values. */
  edit(clave: string, value: string): void {
    this.valoresState.update((valores) => ({ ...valores, [clave]: value }));
    if (this.statusState() === 'rejected' || this.statusState() === 'error') {
      this.rechazoState.set(null);
      this.statusState.set('consent');
    }
  }

  estadoEtapa(etapa: Etapa): EstadoEtapa {
    const indice = ETAPAS.indexOf(etapa);
    const actual = this.etapaState();
    if (indice < actual) {
      return 'done';
    }
    return indice === actual ? 'active' : 'pending';
  }

  /** "Autorizar": the explicit consent that lets Solventa profile the customer. */
  authorize(): void {
    if (!this.canAuthorize()) {
      return;
    }
    this.statusState.set('requesting');
    this.rechazoState.set(null);
    this.etapaState.set(0);
    this.avance?.unsubscribe();
    if (this.etapaMs > 0) {
      this.avance = interval(this.etapaMs)
        .pipe(take(ETAPAS.length - 1))
        .subscribe(() => this.etapaState.update((etapa) => etapa + 1));
    }
    const pausa = this.etapaMs > 0 ? timer(this.etapaMs * ETAPAS.length) : of(0);
    forkJoin([
      this.source({ valor: this.numero('valor'), plazoMeses: this.numero('plazoMeses') }),
      pausa,
    ]).subscribe({
      next: ([oferta]) => {
        this.etapaState.set(ETAPAS.length);
        this.ofertaState.set(oferta);
        this.statusState.set('offer');
      },
      error: (error: unknown) => {
        this.avance?.unsubscribe();
        const rechazo = rechazoDe(error);
        this.rechazoState.set(rechazo);
        this.statusState.set(rechazo ? 'rejected' : 'error');
      },
    });
  }
}
