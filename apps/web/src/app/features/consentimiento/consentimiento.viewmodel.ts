import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';

export type ConsentimientoStatus = 'idle' | 'submitting' | 'error';

export class ConsentimientoViewModel {
  readonly accepted = signal(false);

  private readonly statusState = signal<ConsentimientoStatus>('idle');
  readonly status = this.statusState.asReadonly();

  private readonly attempted = signal(false);

  /** The policy box is left unchecked after an attempt. */
  readonly missing = computed(() => this.attempted() && !this.accepted());

  constructor(
    private readonly grant: () => Observable<unknown>,
    private readonly onGranted: () => void,
  ) {}

  submit(): void {
    if (this.statusState() === 'submitting') {
      return;
    }
    this.attempted.set(true);
    if (!this.accepted()) {
      this.statusState.set('idle');
      return;
    }
    this.statusState.set('submitting');
    this.grant().subscribe({
      next: () => {
        this.statusState.set('idle');
        this.onGranted();
      },
      error: () => this.statusState.set('error'),
    });
  }
}
