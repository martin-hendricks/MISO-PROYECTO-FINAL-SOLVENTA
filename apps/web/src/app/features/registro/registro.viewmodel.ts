import { computed, signal } from '@angular/core';
import { Alta } from './registro.draft';

export type RegistroField = keyof Alta;
export type FieldIssue = 'required' | 'format' | 'length';

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export const MIN_PASSWORD = 8;

export class RegistroViewModel {
  readonly nombre = signal('');
  readonly apellidos = signal('');
  readonly documento = signal('');
  readonly correo = signal('');
  readonly contrasena = signal('');

  private readonly attempted = signal(false);

  readonly issues = computed<Partial<Record<RegistroField, FieldIssue>>>(() => {
    if (!this.attempted()) {
      return {};
    }
    const issues: Partial<Record<RegistroField, FieldIssue>> = {};
    for (const field of ['nombre', 'apellidos', 'documento'] as const) {
      if (!this[field]().trim()) {
        issues[field] = 'required';
      }
    }
    const correo = this.correo().trim();
    if (!correo) {
      issues.correo = 'required';
    } else if (!EMAIL.test(correo)) {
      issues.correo = 'format';
    }
    const contrasena = this.contrasena();
    if (!contrasena) {
      issues.contrasena = 'required';
    } else if (contrasena.length < MIN_PASSWORD) {
      issues.contrasena = 'length';
    }
    return issues;
  });

  constructor(private readonly onContinue: (alta: Alta) => void) {}

  submit(): void {
    this.attempted.set(true);
    if (Object.keys(this.issues()).length) {
      return;
    }
    this.onContinue({
      nombre: this.nombre().trim(),
      apellidos: this.apellidos().trim(),
      documento: this.documento().trim(),
      correo: this.correo().trim(),
      contrasena: this.contrasena(),
    });
  }
}
