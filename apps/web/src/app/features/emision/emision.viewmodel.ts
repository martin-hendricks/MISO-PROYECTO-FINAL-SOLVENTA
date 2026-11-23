import { HttpErrorResponse } from '@angular/common/http';
import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { PolizaResumen } from '../polizas/polizas.gateway';
import { Motivo, ResultadoEmision } from './emision.gateway';

export type EmisionStatus = 'issuing' | 'issued' | 'rejected' | 'expired' | 'revoked' | 'error';

export class EmisionViewModel {
  private readonly statusState = signal<EmisionStatus>('issuing');
  readonly status = this.statusState.asReadonly();

  private readonly polizaState = signal<PolizaResumen | null>(null);
  readonly poliza = this.polizaState.asReadonly();
  readonly renewal = signal(false);

  constructor(
    private readonly source: () => Observable<ResultadoEmision>,
    private readonly onRejected: (motivo: Motivo) => void,
    private readonly onRenewal: (numero: string, enabled: boolean) => Observable<unknown> = () =>
      new Observable((subscriber) => subscriber.complete()),
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
      error: (error: unknown) => {
        const cuerpo = error instanceof HttpErrorResponse ? error.error : null;
        const codigo = cuerpo && typeof cuerpo === 'object' ? String((cuerpo as { codigo?: string }).codigo ?? '') : '';
        const estado = error instanceof HttpErrorResponse ? error.status : 0;
        if (estado === 409 && codigo === 'oferta_vencida') {
          this.statusState.set('expired');
        } else if (estado === 422 && codigo === 'consentimiento_revocado') {
          this.statusState.set('revoked');
        } else {
          this.statusState.set('error');
        }
      },
    });
  }

  chooseRenewal(enabled: boolean): void {
    const poliza = this.polizaState();
    if (!poliza) {
      return;
    }
    this.renewal.set(enabled);
    this.onRenewal(poliza.numero, enabled).subscribe();
  }
}
