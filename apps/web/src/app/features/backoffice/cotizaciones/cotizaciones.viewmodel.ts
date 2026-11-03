import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import {
  CotizacionesFiltro,
  CotizacionesPagina,
  CotizacionPendiente,
} from './cotizaciones.gateway';

export type CotizacionesStatus = 'loading' | 'ready' | 'empty' | 'error';

const POLIZAS_NO_DISPONIBLE = 'polizas_no_disponible';

export class CotizacionesViewModel {
  private readonly statusState = signal<CotizacionesStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly itemsState = signal<CotizacionPendiente[]>([]);
  readonly items = this.itemsState.asReadonly();

  private readonly paginaState = signal(1);
  readonly pagina = this.paginaState.asReadonly();

  private readonly hayMasState = signal(false);
  readonly hayMas = this.hayMasState.asReadonly();

  private readonly incluirVencidasState = signal(false);
  readonly incluirVencidas = this.incluirVencidasState.asReadonly();

  private readonly avisosState = signal<string[]>([]);
  readonly polizasNoVerificadas = computed(() =>
    this.avisosState().includes(POLIZAS_NO_DISPONIBLE),
  );

  constructor(
    private readonly source: (filtro: CotizacionesFiltro) => Observable<CotizacionesPagina>,
  ) {}

  load(): void {
    this.statusState.set('loading');
    this.source({
      incluirVencidas: this.incluirVencidasState(),
      pagina: this.paginaState(),
    }).subscribe({
      next: (respuesta) => {
        this.itemsState.set(respuesta.items);
        this.hayMasState.set(respuesta.hayMas);
        this.avisosState.set(respuesta.avisos);
        this.statusState.set(respuesta.items.length ? 'ready' : 'empty');
      },
      error: () => this.statusState.set('error'),
    });
  }

  toggleVencidas(): void {
    this.incluirVencidasState.update((value) => !value);
    this.paginaState.set(1);
    this.load();
  }

  next(): void {
    this.paginaState.update((pagina) => pagina + 1);
    this.load();
  }

  previous(): void {
    this.paginaState.update((pagina) => pagina - 1);
    this.load();
  }
}
