import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Catalogo, Oferta, RechazoCotizacion, rechazoDe } from './cotizacion.gateway';
import {
  DatosRiesgo,
  datosRiesgo,
  ProblemaCampo,
  Ramo,
  RAMO_INICIAL,
  RAMOS,
  Rango,
  validarCampo,
} from './ramos';

export type CotizacionStatus = 'idle' | 'quoting' | 'quoted' | 'rejected' | 'error';
export type CatalogoStatus = 'loading' | 'ready' | 'error';

/**
 * Risk data capture shared by the customer and advisor quotes. Each line has
 * its own fields; coverages, ranges and options come from the catalog bff-web
 * publishes (HU-2), so invalid input is resolved in place: the field shows the
 * problem, the CTA stays disabled and whatever was typed is kept.
 */
export class CotizacionFormViewModel {
  private readonly ramoState = signal<Ramo>(RAMO_INICIAL);
  readonly ramo = this.ramoState.asReadonly();

  private readonly valoresState = signal<Readonly<Record<string, string>>>({});

  private readonly catalogoState = signal<Catalogo | null>(null);
  private readonly catalogoStatusState = signal<CatalogoStatus>('loading');
  readonly catalogoStatus = this.catalogoStatusState.asReadonly();

  readonly coberturas = computed(() => this.catalogoState()?.coberturas ?? []);
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

  private readonly opcionesState = computed(() => {
    const opciones: Record<string, readonly string[]> = {};
    for (const dato of this.catalogoState()?.datosRiesgo ?? []) {
      if (dato.tipo === 'valores') {
        opciones[dato.nombre] = dato.valores;
      }
    }
    return opciones;
  });

  /** A field the user has left at least once; untouched empty fields show no error yet. */
  private readonly touchedState = signal<ReadonlySet<string>>(new Set());

  private readonly statusState = signal<CotizacionStatus>('idle');
  readonly status = this.statusState.asReadonly();

  private readonly ofertaState = signal<Oferta | null>(null);
  readonly oferta = this.ofertaState.asReadonly();

  private readonly rechazoState = signal<RechazoCotizacion | null>(null);
  readonly rechazo = this.rechazoState.asReadonly();

  /** Field the core rejected (HU-3 names it), until the user edits it. */
  private readonly rejectedField = signal<string | null>(null);

  private readonly problems = computed(() => {
    const problems: Record<string, ProblemaCampo | null> = {};
    for (const campo of this.ramoState().campos) {
      problems[campo.clave] = validarCampo(
        campo,
        this.valor(campo.clave),
        this.rangos()[campo.clave],
        this.opciones(campo.clave),
      );
    }
    return problems;
  });

  readonly valid = computed(
    () =>
      this.catalogoStatusState() === 'ready' &&
      Object.values(this.problems()).every((problem) => problem === null),
  );

  readonly canQuote = computed(() => this.valid() && this.statusState() !== 'quoting');

  constructor(
    private readonly catalogSource: (ramo: string) => Observable<Catalogo>,
    private readonly source: (ramo: string, datos: DatosRiesgo) => Observable<Oferta>,
    private readonly onQuoted: (oferta: Oferta) => void = () => undefined,
    /** Lines this channel offers; the advisor enables more than the customer. */
    readonly ramos: readonly Ramo[] = RAMOS,
  ) {}

  /** Switches line: its own fields start empty and its catalog is loaded. */
  select(id: string): void {
    const ramo = this.ramos.find((r) => r.id === id);
    if (!ramo?.disponible) {
      return;
    }
    this.ramoState.set(ramo);
    this.valoresState.set({});
    this.touchedState.set(new Set());
    this.rejectedField.set(null);
    this.invalidate();
    this.loadCatalog();
  }

  loadCatalog(): void {
    this.catalogoStatusState.set('loading');
    this.catalogoState.set(null);
    this.catalogSource(this.ramoState().ramo).subscribe({
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

  opciones(clave: string): readonly string[] {
    return this.opcionesState()[clave] ?? [];
  }

  /** Problem to show for a field: a typed value that is not valid, or the core's rejection. */
  issue(clave: string): ProblemaCampo | null {
    if (this.rejectedField() === clave) {
      return 'range';
    }
    const typed = this.valor(clave) !== '';
    return typed || this.touchedState().has(clave) ? this.problems()[clave] : null;
  }

  touch(clave: string): void {
    this.touchedState.update((touched) => new Set(touched).add(clave));
  }

  /** Any edit invalidates the offer on screen: the panel degrades to "Sin oferta". */
  edit(clave: string, value: string): void {
    this.valoresState.update((valores) => ({ ...valores, [clave]: value }));
    if (this.rejectedField() === clave) {
      this.rejectedField.set(null);
    }
    this.invalidate();
  }

  /** Drops the offer and any rejection: what is on screen no longer matches the input. */
  invalidate(): void {
    this.ofertaState.set(null);
    this.rechazoState.set(null);
    this.statusState.set('idle');
  }

  quote(): void {
    if (!this.canQuote()) {
      return;
    }
    const ramo = this.ramoState();
    this.statusState.set('quoting');
    this.rechazoState.set(null);
    this.source(ramo.ramo, datosRiesgo(ramo, this.valoresState())).subscribe({
      next: (oferta) => {
        this.ofertaState.set(oferta);
        this.statusState.set('quoted');
        this.onQuoted(oferta);
      },
      error: (error: unknown) => {
        const rechazo = rechazoDe(error);
        this.ofertaState.set(null);
        if (!rechazo) {
          this.statusState.set('error');
          return;
        }
        const clave = /'(\w+)'/.exec(rechazo.mensaje)?.[1];
        this.rechazoState.set(rechazo);
        this.rejectedField.set(ramo.campos.some((c) => c.clave === clave) ? clave! : null);
        this.statusState.set('rejected');
      },
    });
  }
}
