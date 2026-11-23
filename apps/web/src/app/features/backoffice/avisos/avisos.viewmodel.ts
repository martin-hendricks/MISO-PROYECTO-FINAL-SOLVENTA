import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { capturarFocoActivo, restaurarFoco } from '../../../core/a11y/focus-restore';
import { CasoAviso, Cola, FiltroCola, rechazoDelNucleo, ResultadoPago } from './avisos.gateway';

export type ColaStatus = 'loading' | 'ready' | 'empty' | 'error';
export type CasoStatus = 'idle' | 'loading' | 'ready' | 'error';
export type Dialogo = 'aprobar' | 'rechazar' | 'perito' | null;
export type Modo = 'cola' | 'pago';

export interface Puertos {
  cola: (filtro: FiltroCola) => Observable<Cola>;
  caso: (id: string) => Observable<CasoAviso>;
  decidir: (
    id: string,
    decision: 'aprobar' | 'rechazar',
    motivo: string | null,
  ) => Observable<CasoAviso>;
  enrutar: (id: string, motivo: string | null) => Observable<CasoAviso>;
  pagar: (id: string) => Observable<ResultadoPago>;
}

const CONTEOS_VACIOS: Record<FiltroCola, number> = {
  pendientes: 0,
  aprobados: 0,
  rechazados: 0,
  todos: 0,
};

/** HU-26 (cola + detalle en una pantalla), HU-27 (decisión auditada), HU-28 (perito) y
 * HU-29 (pago de bajo monto). Solo llegan a "Pendientes" los casos que el motor no resolvió. */
export class AvisosViewModel {
  readonly filtro = signal<FiltroCola>('pendientes');
  readonly status = signal<ColaStatus>('loading');
  readonly conteos = signal<Record<FiltroCola, number>>(CONTEOS_VACIOS);
  readonly avisos = signal<Cola['avisos']>([]);

  readonly seleccionado = signal<string | null>(null);
  readonly casoStatus = signal<CasoStatus>('idle');
  readonly caso = signal<CasoAviso | null>(null);

  readonly dialogo = signal<Dialogo>(null);
  readonly modo = signal<Modo>('cola');
  readonly enviando = signal(false);
  readonly rechazo = signal<string | null>(null);
  readonly pago = signal<ResultadoPago | null>(null);

  /** Element that had focus when the dialog opened; given back on close. */
  private focoPrevio: HTMLElement | null = null;

  constructor(private readonly puertos: Puertos) {}

  cargar(filtro: FiltroCola = this.filtro()): void {
    this.filtro.set(filtro);
    this.status.set('loading');
    this.puertos.cola(filtro).subscribe({
      next: (cola) => {
        this.conteos.set(cola.conteos);
        this.avisos.set(cola.avisos);
        this.status.set(cola.avisos.length ? 'ready' : 'empty');
        const sigue = cola.avisos.some((a) => a.id === this.seleccionado());
        if (!sigue) {
          // La fila seleccionada ya no está en este chip: se abre el primero o nada.
          const primero = cola.avisos[0]?.id ?? null;
          if (primero) {
            this.seleccionar(primero);
          } else {
            this.seleccionado.set(null);
            this.caso.set(null);
            this.casoStatus.set('idle');
          }
        }
      },
      error: () => this.status.set('error'),
    });
  }

  seleccionar(id: string): void {
    this.seleccionado.set(id);
    this.rechazo.set(null);
    this.casoStatus.set('loading');
    this.puertos.caso(id).subscribe({
      next: (caso) => {
        this.caso.set(caso);
        this.casoStatus.set('ready');
      },
      error: () => this.casoStatus.set('error'),
    });
  }

  abrir(dialogo: Exclude<Dialogo, null>): void {
    this.rechazo.set(null);
    this.focoPrevio = capturarFocoActivo();
    this.dialogo.set(dialogo);
  }

  /** Volver cierra el diálogo SIN cambiar el estado del aviso (Figma HU-27). */
  cerrarDialogo(): void {
    this.dialogo.set(null);
    this.restaurarFocoPrevio();
  }

  /** Gives focus back to the trigger once the dialog is gone. */
  private restaurarFocoPrevio(): void {
    restaurarFoco(this.focoPrevio);
    this.focoPrevio = null;
  }

  confirmar(motivo: string): void {
    const caso = this.caso();
    const dialogo = this.dialogo();
    if (!caso || !dialogo || this.enviando()) {
      return;
    }
    // El diálogo ya bloquea el CTA sin motivo; esta guarda cubre llamadas directas.
    if (dialogo === 'rechazar' && !motivo.trim()) {
      return;
    }
    this.enviando.set(true);
    const motivoONulo = motivo.trim() || null;
    const accion =
      dialogo === 'perito'
        ? this.puertos.enrutar(caso.id, motivoONulo)
        : this.puertos.decidir(caso.id, dialogo, motivoONulo);
    accion.subscribe({
      next: (actualizado) => {
        this.enviando.set(false);
        this.dialogo.set(null);
        this.restaurarFocoPrevio();
        this.caso.set(actualizado);
        // Aprobar un bajo monto encadena con el pago (HU-29).
        if (dialogo === 'aprobar' && actualizado.bajoMonto) {
          this.modo.set('pago');
        }
        this.cargar();
      },
      error: (error: unknown) => {
        this.enviando.set(false);
        this.dialogo.set(null);
        this.restaurarFocoPrevio();
        this.rechazo.set(rechazoDelNucleo(error) ?? 'error');
      },
    });
  }

  abrirPago(): void {
    this.pago.set(null);
    this.rechazo.set(null);
    this.modo.set('pago');
  }

  volverACola(): void {
    this.modo.set('cola');
    this.pago.set(null);
  }

  /** Un reintento devuelve el mismo comprobante; el núcleo garantiza un solo desembolso. */
  pagar(): void {
    const caso = this.caso();
    if (!caso || this.enviando()) {
      return;
    }
    this.enviando.set(true);
    this.rechazo.set(null);
    this.puertos.pagar(caso.id).subscribe({
      next: (resultado) => {
        this.enviando.set(false);
        this.pago.set(resultado);
        this.caso.set(resultado.caso);
        this.cargar();
      },
      error: (error: unknown) => {
        this.enviando.set(false);
        this.rechazo.set(rechazoDelNucleo(error) ?? 'error');
      },
    });
  }

  puedeDecidir(): boolean {
    const caso = this.caso();
    return !!caso && caso.estado === 'en_evaluacion';
  }

  puedePagar(): boolean {
    const caso = this.caso();
    return !!caso && caso.resultado === 'aprobado' && caso.bajoMonto;
  }
}
