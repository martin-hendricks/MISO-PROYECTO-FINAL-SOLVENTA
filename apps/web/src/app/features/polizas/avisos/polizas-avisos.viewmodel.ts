import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { AvisoPoliza } from '../polizas.gateway';

export type PolizasAvisosStatus = 'loading' | 'ready' | 'empty' | 'error';

export class PolizasAvisosViewModel {
  private readonly statusState = signal<PolizasAvisosStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly avisosState = signal<AvisoPoliza[]>([]);
  readonly avisos = this.avisosState.asReadonly();

  constructor(private readonly source: () => Observable<AvisoPoliza[]>) {}

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (avisos) => {
        this.avisosState.set(avisos);
        this.statusState.set(avisos.length ? 'ready' : 'empty');
      },
      error: () => this.statusState.set('error'),
    });
  }
}
