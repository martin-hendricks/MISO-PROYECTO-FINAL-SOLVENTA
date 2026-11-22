import { computed, signal } from '@angular/core';
import { Observable, of, Subscription } from 'rxjs';
import { Cliente } from '../clientes/clientes.gateway';
import { CotizacionFormViewModel } from '../../cotizacion/cotizacion-form.viewmodel';
import { Catalogo, Oferta } from '../../cotizacion/cotizacion.gateway';
import { DatosRiesgo, RAMOS_ASESOR } from '../../cotizacion/ramos';
import { offerExpired } from '../../cotizacion/oferta-expiration';
import { Credito } from '../../vida-crediticia/vida-crediticia.gateway';

/** Motorcycle plate as Colombia issues it: three letters, two digits, one letter (ABC12D). */
const PLACA = /^[A-Z]{3}\d{2}[A-Z]$/;

export type CampoCliente = 'placa';

/**
 * Assisted sale (HU-10): the advisor picks a registered customer and quotes
 * the chosen line on their behalf, so the quote and its policy belong to the
 * customer's real id. Customer data is kept when the line changes.
 */
export class AsesorCotizacionViewModel {
  readonly nombre = signal('');
  readonly documento = signal('');
  readonly placa = signal('');

  readonly form: CotizacionFormViewModel;

  private readonly clienteId = signal<string | null>(null);
  readonly clienteRef = computed(() => this.clienteId() ?? '');
  readonly clienteSeleccionado = computed(() => this.clienteId() !== null);

  readonly busqueda = signal('');
  readonly resultados = signal<readonly Cliente[]>([]);
  readonly buscando = signal(false);
  readonly sinResultados = computed(
    () => this.busqueda().trim().length >= 2 && !this.buscando() && this.resultados().length === 0,
  );
  private busquedaEnCurso?: Subscription;

  /** The plate is SOAT's own datum; no other line asks for it. */
  readonly pidePlaca = computed(() => this.form.ramo().id === 'soat');

  /** Mortgage life is profiled (HU-58): it needs the customer's consent before quoting. */
  readonly esHipotecario = computed(() => this.form.ramo().id === 'hipotecario');
  readonly consentimiento = signal(false);

  private readonly touched = signal<ReadonlySet<CampoCliente>>(new Set());

  private readonly problems = computed<Record<CampoCliente, 'required' | 'format' | null>>(() => ({
    placa:
      !this.pidePlaca() || PLACA.test(this.placa()) ? null : this.placa() ? 'format' : 'required',
  }));

  readonly canQuote = computed(
    () =>
      this.clienteSeleccionado() &&
      Object.values(this.problems()).every((problem) => problem === null) &&
      (!this.esHipotecario() || this.consentimiento()) &&
      this.form.canQuote(),
  );

  /** "Continuar a emisión" needs a firm offer that has not expired. */
  readonly canContinue = computed(() => {
    const oferta = this.form.oferta();
    return !!oferta && !offerExpired(oferta.venceEn, this.now());
  });

  constructor(
    catalogSource: (ramo: string) => Observable<Catalogo>,
    source: (clienteId: string, ramo: string, datos: DatosRiesgo) => Observable<Oferta>,
    hipotecarioSource: (clienteId: string, credito: Credito) => Observable<Oferta>,
    moneda: () => string = () => '',
    private readonly now: () => Date = () => new Date(),
    private readonly searchClients: (q: string) => Observable<readonly Cliente[]> = () => of([]),
  ) {
    this.form = new CotizacionFormViewModel(
      catalogSource,
      (ramo, datos) => {
        if (this.esHipotecario()) {
          const credito = {
            valor: Number(datos['valor']),
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
      moneda,
    );
  }

  /** Prefills the client the advisor opened from Clientes. */
  prefill(clienteId: string, nombre: string, documento: string): void {
    this.clienteId.set(clienteId);
    this.nombre.set(nombre);
    this.documento.set(documento);
  }

  buscar(texto: string): void {
    this.busqueda.set(texto);
    this.busquedaEnCurso?.unsubscribe();
    if (texto.trim().length < 2) {
      this.resultados.set([]);
      this.buscando.set(false);
      return;
    }
    this.buscando.set(true);
    this.busquedaEnCurso = this.searchClients(texto.trim()).subscribe({
      next: (clientes) => {
        this.resultados.set(clientes);
        this.buscando.set(false);
      },
      error: () => {
        this.resultados.set([]);
        this.buscando.set(false);
      },
    });
  }

  /** The customer is part of the quote: picking or changing one drops the offer on screen. */
  seleccionar(cliente: Cliente): void {
    this.prefill(
      cliente.usuarioId,
      `${cliente.nombre} ${cliente.apellidos}`.trim(),
      cliente.documento,
    );
    this.busqueda.set('');
    this.resultados.set([]);
    this.form.invalidate();
  }

  cambiarCliente(): void {
    this.clienteId.set(null);
    this.nombre.set('');
    this.documento.set('');
    this.form.invalidate();
  }

  issue(campo: CampoCliente): 'required' | 'format' | null {
    const problem = this.problems()[campo];
    return this[campo]() !== '' || this.touched().has(campo) ? problem : null;
  }

  touch(campo: CampoCliente): void {
    this.touched.update((touched) => new Set(touched).add(campo));
  }

  edit(campo: CampoCliente, value: string): void {
    this[campo].set(value.toUpperCase().replace(/\s/g, ''));
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
