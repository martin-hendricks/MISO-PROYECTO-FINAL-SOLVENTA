import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { PagoParametrico } from '../siniestros.gateway';

export class ParametricoViewModel {
  private readonly pagoState = signal<PagoParametrico | null>(null);
  readonly pago = this.pagoState.asReadonly();
  readonly renewal = signal(false);

  constructor(
    private readonly source: () => Observable<PagoParametrico>,
    private readonly onRenewal: (numero: string, enabled: boolean) => Observable<unknown>,
  ) {}

  open(): void {
    this.source().subscribe((pago) => this.pagoState.set(pago));
  }

  chooseRenewal(enabled: boolean): void {
    const pago = this.pagoState();
    if (!pago) {
      return;
    }
    this.renewal.set(enabled);
    this.onRenewal(pago.poliza, enabled).subscribe();
  }
}
