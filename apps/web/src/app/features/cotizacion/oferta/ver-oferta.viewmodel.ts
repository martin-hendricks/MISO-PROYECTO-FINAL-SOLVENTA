import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Oferta } from '../cotizacion.gateway';

export type VerOfertaStatus = 'loading' | 'ready' | 'expired' | 'not-found' | 'error';

export class VerOfertaViewModel {
  private readonly statusState = signal<VerOfertaStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly ofertaState = signal<Oferta | null>(null);
  readonly oferta = this.ofertaState.asReadonly();

  constructor(
    private readonly source: () => Observable<Oferta | null>,
    private readonly now: () => Date = () => new Date(),
  ) {}

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (oferta) => {
        this.ofertaState.set(oferta);
        if (!oferta) {
          this.statusState.set('not-found');
          return;
        }
        // HU-7: an expired offer keeps its original price and cannot be accepted.
        const expired = new Date(oferta.venceEn) <= this.now();
        this.statusState.set(expired ? 'expired' : 'ready');
      },
      error: () => this.statusState.set('error'),
    });
  }
}
