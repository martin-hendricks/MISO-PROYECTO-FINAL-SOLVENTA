import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Billetera, Movimiento } from '../billetera.gateway';

export type BilleteraListaStatus = 'loading' | 'ready' | 'empty' | 'error';

export type FiltroBilletera = 'todos' | 'asistido' | 'otras' | 'pago_automatico';

/** A deposit with no currency was stored before the region existed, so it stays in COP. */
function monedaDe(fila: Movimiento): string {
  const codigo = fila.moneda.trim();
  return codigo || 'COP';
}

export class BilleteraListaViewModel {
  private readonly statusState = signal<BilleteraListaStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly filtroState = signal<FiltroBilletera>('todos');
  readonly filtro = this.filtroState.asReadonly();

  private readonly cargadosState = signal<Movimiento[]>([]);

  /** Rows of the active filter. Other currencies stay out of every filter except Otras monedas. */
  readonly movimientos = computed(() => this.filasVisibles());

  /** Sum of the visible rows in the current region. Otras monedas, and an empty filter, have no total. */
  readonly total = computed(() => {
    if (this.filtroState() === 'otras') return null;
    const filas = this.filasVisibles();
    if (filas.length === 0) return null;
    return filas.reduce((suma, fila) => suma + fila.monto, 0);
  });

  /** The region currency, omitted while the customer is looking at the other currencies. */
  readonly moneda = computed(() => (this.filtroState() === 'otras' ? null : this.monedaRegion()));

  constructor(
    private readonly source: () => Observable<Billetera>,
    private readonly monedaRegion: () => string = () => 'COP',
  ) {}

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (billetera) => {
        this.cargadosState.set(billetera.movimientos);
        this.statusState.set(billetera.movimientos.length > 0 ? 'ready' : 'empty');
      },
      error: () => {
        this.cargadosState.set([]);
        this.statusState.set('error');
      },
    });
  }

  seleccionar(filtro: FiltroBilletera): void {
    this.filtroState.set(filtro);
  }

  private filasVisibles(): Movimiento[] {
    const region = this.monedaRegion();
    const filtro = this.filtroState();
    return this.cargadosState().filter((fila) => {
      const enRegion = monedaDe(fila) === region;
      if (filtro === 'otras') return !enRegion;
      if (!enRegion) return false;
      if (filtro === 'asistido') return fila.tipo === 'asistido';
      if (filtro === 'pago_automatico') return fila.tipo === 'pago_automatico';
      return true;
    });
  }
}
