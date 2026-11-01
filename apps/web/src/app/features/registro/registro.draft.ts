import { inject, Injectable, signal } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

/** The sign-up data. It travels to `bff-web` only when the customer grants consent (HU-115). */
export interface Alta {
  nombre: string;
  apellidos: string;
  documento: string;
  correo: string;
  contrasena: string;
}

/**
 * Keeps the sign-up between Registro and consentimiento-datos. Memory only: the password is
 * never written to browser storage, so a reload starts the sign-up again.
 */
@Injectable({ providedIn: 'root' })
export class RegistroDraft {
  private readonly altaState = signal<Alta | null>(null);
  readonly alta = this.altaState.asReadonly();

  save(alta: Alta): void {
    this.altaState.set(alta);
  }

  clear(): void {
    this.altaState.set(null);
  }
}

/** Consent is granted only during the sign-up: without its data the customer starts it again. */
export const requireDraft: CanActivateFn = () =>
  inject(RegistroDraft).alta() !== null || inject(Router).createUrlTree(['/registro']);
