import { of, throwError } from 'rxjs';
import { ASISTIDO, AUTOMATICO, BILLETERA } from '../billetera.testing';
import { BilleteraListaViewModel } from './billetera-lista.viewmodel';

describe('BilleteraListaViewModel', () => {
  it('shows the total and the rows of the current region', () => {
    const vm = new BilleteraListaViewModel(() => of(BILLETERA));
    vm.load();
    expect(vm.status()).toBe('ready');
    expect(vm.moneda()).toBe('COP');
    expect(vm.total()).toBe(1070000);
    expect(vm.movimientos().map((fila) => fila.siniestroId)).toEqual(['SIN-1988', 'SIN-1002']);
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

  it('totals only the deposits in the current region and lists the rest under Otras monedas', () => {
    const enSoles = { ...ASISTIDO, moneda: 'PEN', monto: 381.82, siniestroId: 'SIN-1009' };
    const vm = new BilleteraListaViewModel(
      () =>
        of({
          moneda: null,
          totalRecibido: null,
          movimientos: [enSoles, AUTOMATICO, { ...ASISTIDO, id: 'sin-moneda', moneda: '  ' }],
        }),
      () => 'PEN',
    );
    vm.load();

    expect(vm.moneda()).toBe('PEN');
    expect(vm.total()).toBe(381.82);
    expect(vm.movimientos().map((fila) => fila.siniestroId)).toEqual(['SIN-1009']);

    vm.seleccionar('asistido');
    expect(vm.movimientos().map((fila) => fila.siniestroId)).toEqual(['SIN-1009']);
    vm.seleccionar('pago_automatico');
    expect(vm.movimientos()).toEqual([]);
    expect(vm.total()).toBeNull();

    vm.seleccionar('otras');
    expect(vm.moneda()).toBeNull();
    expect(vm.total()).toBeNull();
    expect(vm.movimientos().map((fila) => fila.moneda.trim() || 'COP')).toEqual(['COP', 'COP']);
  });

  it('keeps a blank currency in COP when that is the region', () => {
    const vm = new BilleteraListaViewModel(() =>
      of({
        moneda: 'COP',
        totalRecibido: null,
        movimientos: [{ ...ASISTIDO, moneda: '' }, { ...AUTOMATICO, moneda: 'MXN' }],
      }),
    );
    vm.load();
    expect(vm.total()).toBe(ASISTIDO.monto);
    expect(vm.movimientos()).toEqual([{ ...ASISTIDO, moneda: '' }]);

    vm.seleccionar('otras');
    expect(vm.movimientos().map((fila) => fila.moneda)).toEqual(['MXN']);
  });
});
