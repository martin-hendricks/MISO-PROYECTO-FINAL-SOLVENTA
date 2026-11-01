import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { PolizaResumen } from '../polizas.gateway';

export type PolizasListaStatus = 'loading' | 'ready' | 'empty' | 'error';

export class PolizasListaViewModel {
  private readonly statusState = signal<PolizasListaStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly polizasState = signal<PolizaResumen[]>([]);
  readonly polizas = this.polizasState.asReadonly();

  constructor(private readonly source: () => Observable<PolizaResumen[]>) {}

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (polizas) => {
        this.polizasState.set(polizas);
        this.statusState.set(polizas.length ? 'ready' : 'empty');
      },
      error: () => this.statusState.set('error'),
    });
  }
}
