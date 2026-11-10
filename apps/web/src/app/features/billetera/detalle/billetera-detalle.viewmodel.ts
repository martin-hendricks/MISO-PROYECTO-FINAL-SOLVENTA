import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Movimiento } from '../billetera.gateway';

export type BilleteraDetalleStatus = 'loading' | 'ready' | 'notFound' | 'error';

export class BilleteraDetalleViewModel {
  private readonly statusState = signal<BilleteraDetalleStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly movimientoState = signal<Movimiento | null>(null);
  readonly movimiento = this.movimientoState.asReadonly();

  constructor(private readonly source: () => Observable<Movimiento | null>) {}

  /** Asistido abre el detalle del aviso. Pago automático abre esa vista. */
  destinoSiniestro(movimiento: Movimiento): string {
    return movimiento.tipo === 'pago_automatico'
      ? '/siniestros/parametrico'
      : `/siniestros/${movimiento.id}`;
  }

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (movimiento) => {
        this.movimientoState.set(movimiento);
        this.statusState.set(movimiento ? 'ready' : 'notFound');
      },
      error: () => {
        this.movimientoState.set(null);
        this.statusState.set('error');
      },
    });
  }
}
