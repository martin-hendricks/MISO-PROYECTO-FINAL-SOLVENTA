import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { SiniestroResumen } from '../siniestros.gateway';

export type SiniestrosListaStatus = 'loading' | 'ready' | 'empty' | 'error';

export class SiniestrosListaViewModel {
  private readonly statusState = signal<SiniestrosListaStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly siniestrosState = signal<SiniestroResumen[]>([]);
  readonly siniestros = this.siniestrosState.asReadonly();

  constructor(private readonly source: () => Observable<SiniestroResumen[]>) {}

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (siniestros) => {
        this.siniestrosState.set(siniestros);
        this.statusState.set(siniestros.length ? 'ready' : 'empty');
      },
      error: () => this.statusState.set('error'),
    });
  }
}
