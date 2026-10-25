import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Catalogo, Oferta, RechazoCotizacion, rechazoDe } from './cotizacion.gateway';
import {
  CAMPO_CIUDAD,
  CampoRango,
  CAMPOS_RANGO,
  DatosRiesgo,
  datosRiesgo,
  ProblemaCampo,
  Rango,
  validarRango,
} from './soat-motocicleta';

export type CotizacionStatus = 'idle' | 'quoting' | 'quoted' | 'rejected' | 'error';
export type CatalogoStatus = 'loading' | 'ready' | 'error';

const esCampoRango = (nombre: string): nombre is CampoRango =>
  (CAMPOS_RANGO as readonly string[]).includes(nombre);

/**
 * Risk data capture shared by the customer and advisor quotes. The valid
 * ranges come from the catalog bff-web publishes (HU-2), so invalid input is
 * resolved in place: the field shows its valid range, the CTA stays disabled
 * and whatever was typed is kept.
 */
export class CotizacionFormViewModel {
  readonly cilindraje = signal('');
  readonly modelo = signal('');
  readonly ciudad = signal('');

  private readonly catalogoState = signal<Catalogo | null>(null);
  private readonly catalogoStatusState = signal<CatalogoStatus>('loading');
  readonly catalogoStatus = this.catalogoStatusState.asReadonly();

  readonly rangos = computed(() => {
    const rangos: Partial<Record<CampoRango, Rango>> = {};
    for (const dato of this.catalogoState()?.datosRiesgo ?? []) {
      if (dato.tipo === 'rango' && esCampoRango(dato.nombre)) {
        rangos[dato.nombre] = { minimo: dato.minimo, maximo: dato.maximo };
      }
    }
    return rangos;
  });

  readonly ciudades = computed(() => {
    const dato = this.catalogoState()?.datosRiesgo.find((d) => d.nombre === CAMPO_CIUDAD);
    return dato?.tipo === 'valores' ? dato.valores : [];
  });

  /** A field the user has left at least once; untouched empty fields show no error yet. */
  private readonly touchedState = signal<ReadonlySet<CampoRango>>(new Set());

  private readonly statusState = signal<CotizacionStatus>('idle');
  readonly status = this.statusState.asReadonly();

  private readonly ofertaState = signal<Oferta | null>(null);
  readonly oferta = this.ofertaState.asReadonly();

  private readonly rechazoState = signal<RechazoCotizacion | null>(null);
  readonly rechazo = this.rechazoState.asReadonly();

  /** Field the core rejected (HU-3 names it), until the user edits it. */
  private readonly rejectedField = signal<CampoRango | null>(null);

  private readonly problems = computed<Record<CampoRango, ProblemaCampo | null>>(() => ({
    cilindraje_cc: validarRango(this.rangos().cilindraje_cc, this.cilindraje()),
    modelo_anio: validarRango(this.rangos().modelo_anio, this.modelo()),
  }));

  readonly valid = computed(
    () =>
      this.catalogoStatusState() === 'ready' &&
      Object.values(this.problems()).every((problem) => problem === null) &&
      !!this.ciudad(),
  );

  readonly canQuote = computed(() => this.valid() && this.statusState() !== 'quoting');

  constructor(
    private readonly catalogSource: () => Observable<Catalogo>,
    private readonly source: (datos: DatosRiesgo) => Observable<Oferta>,
    private readonly onQuoted: (oferta: Oferta) => void = () => undefined,
  ) {}

  loadCatalog(): void {
    this.catalogoStatusState.set('loading');
    this.catalogSource().subscribe({
      next: (catalogo) => {
        this.catalogoState.set(catalogo);
        if (!this.ciudad()) {
          this.ciudad.set(this.ciudades()[0] ?? '');
        }
        this.catalogoStatusState.set('ready');
      },
      error: () => this.catalogoStatusState.set('error'),
    });
  }

  /** Problem to show for a field: a typed value out of range, or the core's rejection. */
  issue(campo: CampoRango): ProblemaCampo | null {
    if (this.rejectedField() === campo) {
      return 'range';
    }
    const problem = this.problems()[campo];
    const typed = (campo === 'cilindraje_cc' ? this.cilindraje() : this.modelo()) !== '';
    return typed || this.touchedState().has(campo) ? problem : null;
  }

  touch(campo: CampoRango): void {
    this.touchedState.update((touched) => new Set(touched).add(campo));
  }

  /** Any edit invalidates the offer on screen: the panel degrades to "Sin oferta". */
  edit(campo: CampoRango | 'ciudad', value: string): void {
    if (campo === 'cilindraje_cc') {
      this.cilindraje.set(value);
    } else if (campo === 'modelo_anio') {
      this.modelo.set(value);
    } else {
      this.ciudad.set(value);
    }
    if (this.rejectedField() === campo) {
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
    this.statusState.set('quoting');
    this.rechazoState.set(null);
    const datos = datosRiesgo({
      cilindraje: this.cilindraje(),
      modelo: this.modelo(),
      ciudad: this.ciudad(),
    });
    this.source(datos).subscribe({
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
        const campo = /'(\w+)'/.exec(rechazo.mensaje)?.[1] ?? '';
        this.rechazoState.set(rechazo);
        this.rejectedField.set(esCampoRango(campo) ? campo : null);
        this.statusState.set('rejected');
      },
    });
  }
}
