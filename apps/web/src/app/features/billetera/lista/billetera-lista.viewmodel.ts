import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Billetera, Movimiento } from '../billetera.gateway';

export type BilleteraListaStatus = 'loading' | 'ready' | 'empty' | 'error';

export class BilleteraListaViewModel {
  private readonly statusState = signal<BilleteraListaStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly totalState = signal<number | null>(null);
  readonly total = this.totalState.asReadonly();

  private readonly monedaState = signal('COP');
  readonly moneda = this.monedaState.asReadonly();

  private readonly movimientosState = signal<Movimiento[]>([]);
  readonly movimientos = this.movimientosState.asReadonly();

  constructor(private readonly source: () => Observable<Billetera>) {}

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (billetera) => {
        const conDepositos = billetera.movimientos.length > 0;
        this.totalState.set(conDepositos ? billetera.totalRecibido : null);
        this.monedaState.set(billetera.moneda);
        this.movimientosState.set(billetera.movimientos);
        this.statusState.set(conDepositos ? 'ready' : 'empty');
      },
      error: () => {
        this.totalState.set(null);
        this.movimientosState.set([]);
        this.statusState.set('error');
      },
    });
  }
}
