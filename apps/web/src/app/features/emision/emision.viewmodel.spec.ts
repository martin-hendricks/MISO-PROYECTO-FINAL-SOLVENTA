import { of, throwError } from 'rxjs';
import { EMITIDA } from './emision.testing';
import { EmisionViewModel } from './emision.viewmodel';

describe('EmisionViewModel', () => {
  it('keeps renewal off until the customer changes it, without another issuance', () => {
    const issued = of(EMITIDA);
    const saved: boolean[] = [];
    const vm = new EmisionViewModel(
      () => issued,
      () => fail('should not reject'),
      (_numero, enabled) => {
        saved.push(enabled);
        return of({ numero: 'POL-2026-00088421', renovacionAutomatica: enabled });
      },
    );
    vm.issue();
    expect(vm.status()).toBe('issued');
    expect(vm.renewal()).toBeFalse();
    expect(saved).toEqual([]);
    vm.chooseRenewal(true);
    expect(saved).toEqual([true]);
  });

  it('records rejection and transport failure without a renewal callback', () => {
    const issued = new EmisionViewModel(() => of(EMITIDA), () => undefined);
    issued.issue();
    issued.chooseRenewal(true);
    expect(issued.renewal()).toBeTrue();

    const rejected = new EmisionViewModel(
      () => of({ resultado: 'RECHAZADA', motivo: { codigo: 'x', mensaje: 'no' } }),
      () => undefined,
    );
    rejected.issue();
    expect(rejected.status()).toBe('rejected');
    rejected.chooseRenewal(true);

    const failed = new EmisionViewModel(
      () => throwError(() => new Error('network')),
      () => undefined,
    );
    failed.issue();
    expect(failed.status()).toBe('error');
  });
});
