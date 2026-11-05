import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { CotizacionFormViewModel } from '../../cotizacion/cotizacion-form.viewmodel';
import { Catalogo, Oferta } from '../../cotizacion/cotizacion.gateway';
import { DatosRiesgo, RAMOS_ASESOR } from '../../cotizacion/ramos';
import { Credito } from '../../vida-crediticia/vida-crediticia.gateway';

/** Motorcycle plate as Colombia issues it: three letters, two digits, one letter (ABC12D). */
const PLACA = /^[A-Z]{3}\d{2}[A-Z]$/;

export type CampoCliente = 'nombre' | 'documento' | 'placa';

/**
 * Assisted sale (HU-10): the advisor captures the customer and the risk of
 * the chosen line, and quotes on the customer's behalf. Customer data is kept
 * when the line changes. Without a customer search (out of scope), the
 * identity document is the id the quote is tied to.
 */
export class AsesorCotizacionViewModel {
  readonly nombre = signal('');
  readonly documento = signal('');
  readonly placa = signal('');

  readonly form: CotizacionFormViewModel;

  /** Real id of a client opened from Clientes; the document stands in otherwise. */
  private readonly clienteId = signal<string | null>(null);
  readonly clienteRef = computed(() => this.clienteId() ?? this.documento());

  /** The plate is SOAT's own datum; no other line asks for it. */
  readonly pidePlaca = computed(() => this.form.ramo().id === 'soat');

  /** Mortgage life is profiled (HU-58): it needs the customer's consent before quoting. */
  readonly esHipotecario = computed(() => this.form.ramo().id === 'hipotecario');
  readonly consentimiento = signal(false);

  private readonly touched = signal<ReadonlySet<CampoCliente>>(new Set());

  private readonly problems = computed<Record<CampoCliente, 'required' | 'format' | null>>(() => ({
    nombre: this.nombre().trim() ? null : 'required',
    documento: /^\d{5,12}$/.test(this.documento())
      ? null
      : this.documento()
        ? 'format'
        : 'required',
    placa:
      !this.pidePlaca() || PLACA.test(this.placa()) ? null : this.placa() ? 'format' : 'required',
  }));

  readonly canQuote = computed(
    () =>
      Object.values(this.problems()).every((problem) => problem === null) &&
      (!this.esHipotecario() || this.consentimiento()) &&
      this.form.canQuote(),
  );

  /** "Continuar a emisión" needs a firm offer that has not expired. */
  readonly canContinue = computed(() => {
    const oferta = this.form.oferta();
    return !!oferta && new Date(oferta.venceEn) > this.now();
  });

  constructor(
    catalogSource: (ramo: string) => Observable<Catalogo>,
    source: (clienteId: string, ramo: string, datos: DatosRiesgo) => Observable<Oferta>,
    hipotecarioSource: (clienteId: string, credito: Credito) => Observable<Oferta>,
    private readonly now: () => Date = () => new Date(),
  ) {
    this.form = new CotizacionFormViewModel(
      catalogSource,
      (ramo, datos) => {
        if (this.esHipotecario()) {
          const credito = {
            valor: Number(datos['valorCredito']),
            plazoMeses: Number(datos['plazoMeses']),
          };
          return hipotecarioSource(this.clienteRef(), credito);
        }
        return source(
          this.clienteRef(),
          ramo,
          this.pidePlaca() ? { ...datos, placa: this.placa() } : datos,
        );
      },
      undefined,
      RAMOS_ASESOR,
    );
  }

  /** Prefills the client the advisor opened from Clientes. */
  prefill(clienteId: string, nombre: string, documento: string): void {
    this.clienteId.set(clienteId);
    this.nombre.set(nombre);
    this.documento.set(documento);
  }

  issue(campo: CampoCliente): 'required' | 'format' | null {
    const problem = this.problems()[campo];
    return this[campo]() !== '' || this.touched().has(campo) ? problem : null;
  }

  touch(campo: CampoCliente): void {
    this.touched.update((touched) => new Set(touched).add(campo));
  }

  /** Customer data is part of the quote: editing it also drops the offer on screen. */
  edit(campo: CampoCliente, value: string): void {
    this[campo].set(campo === 'placa' ? value.toUpperCase().replace(/\s/g, '') : value);
    if (campo === 'documento') {
      this.clienteId.set(null);
    }
    this.form.invalidate();
  }

  /** The consent belongs to the quote: changing it also drops the offer on screen. */
  consentir(value: boolean): void {
    this.consentimiento.set(value);
    this.form.invalidate();
  }

  quote(): void {
    if (this.canQuote()) {
      this.form.quote();
    }
  }
}
