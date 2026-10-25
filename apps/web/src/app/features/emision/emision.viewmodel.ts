import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { PolizaResumen } from '../polizas/polizas.gateway';
import { Motivo, ResultadoEmision } from './emision.gateway';

export type EmisionStatus = 'issuing' | 'issued' | 'rejected' | 'error';

export class EmisionViewModel {
  private readonly statusState = signal<EmisionStatus>('issuing');
  readonly status = this.statusState.asReadonly();

  private readonly polizaState = signal<PolizaResumen | null>(null);
  readonly poliza = this.polizaState.asReadonly();

  constructor(
    private readonly source: () => Observable<ResultadoEmision>,
    private readonly onRejected: (motivo: Motivo) => void,
  ) {}

  issue(): void {
    this.statusState.set('issuing');
    this.source().subscribe({
      next: (resultado) => {
        if (resultado.resultado === 'EMITIDA') {
          this.polizaState.set(resultado.poliza);
          this.statusState.set('issued');
        } else {
          this.statusState.set('rejected');
          this.onRejected(resultado.motivo);
        }
      },
      error: () => this.statusState.set('error'),
    });
  }
}
