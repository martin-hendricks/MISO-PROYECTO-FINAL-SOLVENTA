import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Inicio } from './inicio.gateway';

export type InicioStatus = 'loading' | 'ready' | 'empty' | 'error';

/** What Inicio is allowed to draw. Each slot is independent of the others. */
export interface InicioPanel {
  offer: Inicio['ofertaVigente'];
  policy: Inicio['poliza'];
  claim: Inicio['siniestroEnCurso'];
  vidaCrediticia: boolean;
}

const NO_CARDS: InicioPanel = { offer: null, policy: null, claim: null, vidaCrediticia: false };

export class InicioViewModel {
  private readonly statusState = signal<InicioStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly inicioState = signal<Inicio | null>(null);

  readonly panel = computed<InicioPanel>(() => {
    const inicio = this.inicioState();
    if (!inicio) {
      return NO_CARDS;
    }
    return {
      offer: inicio.ofertaVigente?.cotizacionId ? inicio.ofertaVigente : null,
      policy: inicio.poliza?.estado === 'vigente' ? inicio.poliza : null,
      claim: inicio.siniestroEnCurso ?? null,
      vidaCrediticia: inicio.hipotecario != null,
    };
  });

  constructor(private readonly source: () => Observable<Inicio>) {}

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (inicio) => {
        this.inicioState.set(inicio);
        const { offer, policy, claim, vidaCrediticia } = this.panel();
        this.statusState.set(offer || policy || claim || vidaCrediticia ? 'ready' : 'empty');
      },
      error: () => this.statusState.set('error'),
    });
  }
}
