import { of, throwError } from 'rxjs';
import { ASISTIDO, AUTOMATICO, BILLETERA } from '../billetera.testing';
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

  it('keeps a null total null when the deposits use more than one currency', () => {
    const vm = new BilleteraListaViewModel(() =>
      of({
        moneda: null,
        totalRecibido: null,
        movimientos: [ASISTIDO, { ...AUTOMATICO, moneda: 'MXN' }],
      }),
    );
    vm.load();
    expect(vm.status()).toBe('ready');
    expect(vm.total()).toBeNull();
    expect(vm.moneda()).toBeNull();
    expect(vm.movimientos().map((fila) => fila.moneda)).toEqual(['COP', 'MXN']);
  });
});
