import { computed, signal } from '@angular/core';
import {
  formatGroupedCop,
  incomeWire,
  moneyDigits,
  spendingWire,
  wireAmount,
} from '../../core/i18n/money-input';
import { Alta } from './registro.draft';

export type RegistroField = keyof Alta;
export type FieldIssue = 'required' | 'format' | 'length' | 'amount';

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export const MIN_PASSWORD = 8;

export class RegistroViewModel {
  readonly nombre = signal('');
  readonly apellidos = signal('');
  readonly documento = signal('');
  readonly correo = signal('');
  readonly contrasena = signal('');
  readonly ingresos = signal('');
  readonly gastos = signal('');
  readonly incomeDisplay = computed(() => formatGroupedCop(this.ingresos()));
  readonly spendingDisplay = computed(() => formatGroupedCop(this.gastos()));

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
    if (!incomeWire(this.ingresos())) {
      issues.ingresos_mensuales = this.ingresos() ? 'amount' : 'required';
    }
    if (!spendingWire(this.gastos())) {
      issues.gastos_mensuales = 'required';
    }
    return issues;
  });

  setIncome(raw: string): void {
    this.ingresos.set(moneyDigits(raw));
  }

  setSpending(raw: string): void {
    this.gastos.set(moneyDigits(raw));
  }

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
      ingresos_mensuales: wireAmount(this.ingresos())!,
      gastos_mensuales: wireAmount(this.gastos())!,
    });
  }
}
