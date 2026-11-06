import { computed, signal } from '@angular/core';
import {
  cardDigits,
  cardFranchise,
  cardReady,
  expiryMonth,
  expiryYear,
  groupCard,
} from './card-confirmation';

/** Local confirmation only. Nothing here is a Solventa request field. */
export class ConfirmacionTarjetaViewModel {
  private readonly holderState = signal('');
  readonly holder = this.holderState.asReadonly();
  private readonly numberState = signal('');
  readonly number = this.numberState.asReadonly();
  private readonly monthState = signal('');
  readonly month = this.monthState.asReadonly();
  private readonly yearState = signal('');
  readonly year = this.yearState.asReadonly();
  private readonly codeState = signal('');
  readonly code = this.codeState.asReadonly();

  readonly grouped = computed(() => groupCard(this.number()));
  readonly numberHint = computed(() => {
    const franchise = cardFranchise(this.number());
    if (franchise === 'amex') {
      return 'tarjeta.numeroHint.amex';
    }
    if (franchise === 'diners') {
      return 'tarjeta.numeroHint.diners';
    }
    return 'tarjeta.numeroHint.default';
  });
  readonly ready = computed(() =>
    cardReady({
      holder: this.holder(),
      digits: this.number(),
      month: this.month(),
      year: this.year(),
      code: this.code(),
    }),
  );

  setHolder(value: string): void {
    this.holderState.set(value);
  }

  setNumber(value: string): void {
    this.numberState.set(cardDigits(value));
  }

  setMonth(value: string): void {
    this.monthState.set(expiryMonth(value));
  }

  setYear(value: string): void {
    this.yearState.set(expiryYear(value));
  }

  setCode(value: string): void {
    this.codeState.set(value.replace(/\D/g, '').slice(0, 4));
  }

  clear(): void {
    this.holderState.set('');
    this.numberState.set('');
    this.monthState.set('');
    this.yearState.set('');
    this.codeState.set('');
  }
}
