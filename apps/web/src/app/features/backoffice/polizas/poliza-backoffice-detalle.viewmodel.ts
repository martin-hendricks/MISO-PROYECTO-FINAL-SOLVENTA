import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { PolizaOperador, rechazoDePoliza } from './polizas-backoffice.gateway';

export type PolizaBackofficeStatus = 'loading' | 'ready' | 'not-found' | 'error';
export type AccionPoliza = 'idle' | 'enviando' | 'hecho' | 'rechazado';

export class PolizaBackofficeDetalleViewModel {
  private readonly statusState = signal<PolizaBackofficeStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly polizaState = signal<PolizaOperador | null>(null);
  readonly poliza = this.polizaState.asReadonly();

  private readonly accionState = signal<AccionPoliza>('idle');
  readonly accion = this.accionState.asReadonly();

  private readonly rechazoState = signal<string | null>(null);
  readonly rechazo = this.rechazoState.asReadonly();

  constructor(
    private readonly source: () => Observable<PolizaOperador | null>,
    private readonly renovarSource: () => Observable<PolizaOperador>,
    private readonly cancelarSource: (motivo: string) => Observable<PolizaOperador>,
  ) {}

  load(): void {
    this.statusState.set('loading');
    this.accionState.set('idle');
    this.source().subscribe({
      next: (poliza) => {
        this.polizaState.set(poliza);
        this.statusState.set(poliza ? 'ready' : 'not-found');
      },
      error: () => this.statusState.set('error'),
    });
  }

  renovar(): void {
    this.accionState.set('enviando');
    this.renovarSource().subscribe({
      next: (poliza) => {
        this.polizaState.set(poliza);
        this.accionState.set('hecho');
      },
      error: (error: unknown) => {
        const rechazo = rechazoDePoliza(error);
        this.rechazoState.set(rechazo?.mensaje ?? null);
        this.accionState.set(rechazo ? 'rechazado' : 'idle');
      },
    });
  }

  cancelar(motivo: string): void {
    this.accionState.set('enviando');
    this.cancelarSource(motivo).subscribe({
      next: (poliza) => {
        this.polizaState.set(poliza);
        this.accionState.set('hecho');
      },
      error: (error: unknown) => {
        const rechazo = rechazoDePoliza(error);
        this.rechazoState.set(rechazo?.mensaje ?? null);
        this.accionState.set(rechazo ? 'rechazado' : 'idle');
      },
    });
  }
}
