import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Catalogo, RechazoCotizacion, rechazoDe } from '../cotizacion/cotizacion.gateway';
import { Campo, ProblemaCampo, Rango, validarCampo } from '../cotizacion/ramos';
import { Credito, OfertaHipotecaria } from './vida-crediticia.gateway';

export type VidaCrediticiaStatus = 'consent' | 'requesting' | 'offer' | 'rejected' | 'error';
export type CatalogoStatus = 'loading' | 'ready' | 'error';

/** The mortgage data, with the keys of the `vida-crediticia` catalog that bounds them. */
export const CAMPOS_CREDITO: readonly Campo[] = [
  { clave: 'valorCredito', tipo: 'moneda' },
  { clave: 'plazoMeses', tipo: 'numero' },
];

/**
 * Mortgage life origination (HU-105): the customer gives the mortgage data and
 * authorizes profiling in one step; "Ahora no" leaves without calling anyone.
 * The offer is a firm quote, so accepting it goes to the regular emission.
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

  /** "Autorizar": the explicit consent that lets Solventa profile the customer. */
  authorize(): void {
    if (!this.canAuthorize()) {
      return;
    }
    this.statusState.set('requesting');
    this.rechazoState.set(null);
    this.source({
      valor: this.numero('valorCredito'),
      plazoMeses: this.numero('plazoMeses'),
    }).subscribe({
      next: (oferta) => {
        this.ofertaState.set(oferta);
        this.statusState.set('offer');
      },
      error: (error: unknown) => {
        const rechazo = rechazoDe(error);
        this.rechazoState.set(rechazo);
        this.statusState.set(rechazo ? 'rejected' : 'error');
      },
    });
  }
}
