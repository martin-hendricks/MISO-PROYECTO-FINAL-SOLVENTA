import { of, throwError } from 'rxjs';
import { BILLETERA } from '../billetera.testing';
import { BilleteraListaViewModel } from './billetera-lista.viewmodel';

describe('BilleteraListaViewModel', () => {
  it('shows the total and the rows', () => {
    const vm = new BilleteraListaViewModel(() => of(BILLETERA));
    vm.load();
    expect(vm.status()).toBe('ready');
    expect(vm.total()).toBe(1070000);
    expect(vm.movimientos().length).toBe(2);
  });

  it('is empty without deposits and does not invent a zero total on error', () => {
    const vacia = new BilleteraListaViewModel(() =>
      of({ moneda: 'COP', totalRecibido: 0, movimientos: [] }),
    );
    vacia.load();
    expect(vacia.status()).toBe('empty');
    expect(vacia.total()).toBeNull();

    let attempts = 0;
    const error = new BilleteraListaViewModel(() => {
      attempts += 1;
      return attempts === 1 ? throwError(() => new Error('caido')) : of(BILLETERA);
    });
    error.load();
    expect(error.status()).toBe('error');
    expect(error.total()).toBeNull();
    expect(error.movimientos()).toEqual([]);

    error.load();
    expect(error.status()).toBe('ready');
    expect(error.total()).toBe(1070000);
  });
});
