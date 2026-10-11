import { HttpErrorResponse } from '@angular/common/http';
import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Credentials } from '../../core/session/session.service';

export type LoginStatus = 'idle' | 'submitting' | 'error';
export type LoginFailure = 'credentials' | 'network';
export type EmailIssue = 'required' | 'format';

export interface SignIn {
  signIn(credentials: Credentials): Observable<void>;
}

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export class LoginViewModel {
  readonly email = signal('');
  readonly password = signal('');

  private readonly statusState = signal<LoginStatus>('idle');
  readonly status = this.statusState.asReadonly();

  private readonly failureState = signal<LoginFailure | null>(null);
  readonly failure = this.failureState.asReadonly();

  private readonly attempted = signal(false);

  readonly emailIssue = computed<EmailIssue | null>(() => {
    if (!this.attempted()) {
      return null;
    }
    const email = this.email().trim();
    if (!email) {
      return 'required';
    }
    return EMAIL.test(email) ? null : 'format';
  });

  readonly passwordMissing = computed(() => this.attempted() && !this.password());

  constructor(
    private readonly session: SignIn,
    private readonly onSignedIn: () => void,
  ) {}

  submit(): void {
    if (this.statusState() === 'submitting') {
      return;
    }
    this.attempted.set(true);
    this.failureState.set(null);
    if (this.emailIssue() || this.passwordMissing()) {
      this.statusState.set('idle');
      return;
    }
    this.statusState.set('submitting');
    this.session
      .signIn({ email: this.email().trim(), password: this.password(), role: 'cliente' })
      .subscribe({
        next: () => {
          this.statusState.set('idle');
          this.onSignedIn();
        },
        error: (error: unknown) => {
          const unauthorized = error instanceof HttpErrorResponse && error.status === 401;
          this.failureState.set(unauthorized ? 'credentials' : 'network');
          this.statusState.set('error');
        },
      });
  }
}
