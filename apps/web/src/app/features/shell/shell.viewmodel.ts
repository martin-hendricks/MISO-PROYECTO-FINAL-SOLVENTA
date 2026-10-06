import { signal } from '@angular/core';

export type ShellStatus = 'idle' | 'ready';

export class ShellViewModel {
  private readonly statusState = signal<ShellStatus>('idle');
  readonly status = this.statusState.asReadonly();

  activate(): void {
    this.statusState.set('ready');
  }
}
