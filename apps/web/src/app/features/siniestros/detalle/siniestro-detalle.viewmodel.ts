import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { SiniestroDetalle } from '../siniestros.gateway';

export type SiniestroDetalleStatus = 'loading' | 'ready' | 'not-found' | 'error';

export class SiniestroDetalleViewModel {
  private readonly statusState = signal<SiniestroDetalleStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly siniestroState = signal<SiniestroDetalle | null>(null);
  readonly siniestro = this.siniestroState.asReadonly();

  constructor(private readonly source: () => Observable<SiniestroDetalle | null>) {}

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (siniestro) => {
        this.siniestroState.set(siniestro);
        this.statusState.set(siniestro ? 'ready' : 'not-found');
      },
      error: () => this.statusState.set('error'),
    });
  }
}
