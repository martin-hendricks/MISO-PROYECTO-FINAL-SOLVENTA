import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Oferta, SolicitudCotizacion, TipoDispositivo } from './cotizacion.gateway';

export type CotizacionStatus = 'idle' | 'submitting' | 'ready' | 'error';

export interface CotizacionForm {
  nombre: string;
  documento: string;
  vigenciaMeses: number;
  tipo: TipoDispositivo;
  valorAsegurado: string;
  marca: string;
  modelo: string;
}

export interface Quotes {
  quote(solicitud: SolicitudCotizacion): Observable<Oferta>;
  find(cotizacionId: string): Observable<Oferta>;
}

export const VIGENCIAS = [12, 24] as const;
export const TIPOS: readonly TipoDispositivo[] = ['telefono', 'tablet', 'portatil'];
export const VALOR_ASEGURADO = { min: 200_000, max: 8_000_000, moneda: 'COP' } as const;

const EMPTY: CotizacionForm = {
  nombre: '',
  documento: '',
  vigenciaMeses: VIGENCIAS[0],
  tipo: TIPOS[0],
  valorAsegurado: '',
  marca: '',
  modelo: '',
};

export class CotizacionViewModel {
  private readonly formState = signal<CotizacionForm>(EMPTY);
  readonly form = this.formState.asReadonly();

  private readonly statusState = signal<CotizacionStatus>('idle');
  readonly status = this.statusState.asReadonly();

  private readonly offerState = signal<Oferta | null>(null);
  readonly offer = this.offerState.asReadonly();

  readonly valorOutOfRange = computed(() => {
    const raw = this.formState().valorAsegurado.trim();
    if (!raw) {
      return false;
    }
    const valor = Number(raw);
    return !Number.isInteger(valor) || valor < VALOR_ASEGURADO.min || valor > VALOR_ASEGURADO.max;
  });

  private readonly complete = computed(() => {
    const form = this.formState();
    return [form.nombre, form.documento, form.valorAsegurado, form.marca, form.modelo].every(
      (value) => value.trim(),
    );
  });

  readonly canCalculate = computed(
    () => this.complete() && !this.valorOutOfRange() && this.statusState() !== 'submitting',
  );

  readonly canIssue = computed(() => this.offerState()?.estado === 'oferta_vigente');

  constructor(private readonly quotes: Quotes) {}

  /** Any edit drops the offer: it no longer prices what the form says. */
  patch(change: Partial<CotizacionForm>): void {
    if (this.statusState() === 'submitting') {
      return;
    }
    this.formState.update((form) => ({ ...form, ...change }));
    this.offerState.set(null);
    this.statusState.set('idle');
  }

  clear(): void {
    this.patch(EMPTY);
  }

  /** Asking again for an unchanged form reads the same quote by id instead of pricing a new one. */
  calculate(): void {
    if (!this.canCalculate()) {
      return;
    }
    const current = this.offerState();
    this.statusState.set('submitting');
    const answer = current
      ? this.quotes.find(current.cotizacionId)
      : this.quotes.quote(this.request());
    answer.subscribe({
      next: (offer) => {
        this.offerState.set(offer);
        this.statusState.set('ready');
      },
      error: () => this.statusState.set('error'),
    });
  }

  private request(): SolicitudCotizacion {
    const form = this.formState();
    return {
      cliente: { nombre: form.nombre.trim(), documento: form.documento.trim() },
      ramo: 'dispositivo',
      vigenciaMeses: form.vigenciaMeses,
      datosRiesgo: {
        tipo: form.tipo,
        valorAsegurado: Number(form.valorAsegurado.trim()),
        marca: form.marca.trim(),
        modelo: form.modelo.trim(),
      },
    };
  }
}
