import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Conteo } from './metricas.gateway';

export type MetricasStatus = 'loading' | 'ready' | 'empty' | 'error';

export class MetricasViewModel {
  private readonly statusState = signal<MetricasStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly conteosState = signal<Conteo[]>([]);
  readonly conteos = this.conteosState.asReadonly();

  constructor(private readonly source: (desde: string, hasta: string) => Observable<Conteo[]>) {}

  load(desde: string, hasta: string): void {
    this.statusState.set('loading');
    this.source(desde, hasta).subscribe({
      next: (conteos) => {
        this.conteosState.set(conteos);
        this.statusState.set(conteos.length ? 'ready' : 'empty');
      },
      error: () => this.statusState.set('error'),
    });
  }
}
