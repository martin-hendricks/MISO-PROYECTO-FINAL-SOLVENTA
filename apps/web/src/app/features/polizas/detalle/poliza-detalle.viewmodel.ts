import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { PolizaDetalle } from '../polizas.gateway';

export type PolizaDetalleStatus = 'loading' | 'ready' | 'not-found' | 'error';

export class PolizaDetalleViewModel {
  private readonly statusState = signal<PolizaDetalleStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly polizaState = signal<PolizaDetalle | null>(null);
  readonly poliza = this.polizaState.asReadonly();

  constructor(private readonly source: () => Observable<PolizaDetalle | null>) {}

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (poliza) => {
        this.polizaState.set(poliza);
        this.statusState.set(poliza ? 'ready' : 'not-found');
      },
      error: () => this.statusState.set('error'),
    });
  }
}
