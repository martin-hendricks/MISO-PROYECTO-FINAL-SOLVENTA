import { HttpErrorResponse } from '@angular/common/http';
import { of, Subject, throwError } from 'rxjs';
import { CotizacionFormViewModel } from './cotizacion-form.viewmodel';
import { Oferta } from './cotizacion.gateway';
import { FUERA_DE_RANGO, fueraDeRango, OFERTA } from './cotizacion.testing';

describe('CotizacionFormViewModel', () => {
  function filled(vm: CotizacionFormViewModel) {
    vm.edit('cilindraje_cc', '150');
    vm.edit('modelo_anio', '2022');
    vm.edit('ciudad', 'medellin');
    return vm;
  }

  it('sends the risk data with the names the core catalog expects', () => {
    const source = jasmine.createSpy('source').and.returnValue(of(OFERTA));
    const onQuoted = jasmine.createSpy('onQuoted');
    const vm = filled(new CotizacionFormViewModel(source, onQuoted));

    vm.quote();

    expect(source).toHaveBeenCalledOnceWith({
      cilindraje_cc: 150,
      modelo_anio: 2022,
      ciudad_circulacion: 'medellin',
    });
    expect(vm.status()).toBe('quoted');
    expect(vm.oferta()).toEqual(OFERTA);
    expect(onQuoted).toHaveBeenCalledOnceWith(OFERTA);
  });

  it('works without a quoted callback', () => {
    const vm = filled(new CotizacionFormViewModel(() => of(OFERTA)));

    vm.quote();

    expect(vm.status()).toBe('quoted');
  });

  it('blocks the quote while a value is out of its catalog range', () => {
    const source = jasmine.createSpy('source');
    const vm = filled(new CotizacionFormViewModel(source));

    vm.edit('cilindraje_cc', '2500');
    vm.quote();

    expect(vm.issue('cilindraje_cc')).toBe('range');
    expect(vm.canQuote()).toBeFalse();
    expect(source).not.toHaveBeenCalled();
    expect(vm.cilindraje()).toBe('2500');
  });

  it('rejects decimals and keeps empty untouched fields quiet until left', () => {
    const vm = new CotizacionFormViewModel(() => of(OFERTA));

    expect(vm.issue('modelo_anio')).toBeNull();
    vm.touch('modelo_anio');
    expect(vm.issue('modelo_anio')).toBe('required');
    vm.edit('modelo_anio', '2020.5');
    expect(vm.issue('modelo_anio')).toBe('range');
    expect(vm.canQuote()).toBeFalse();
  });

  it('disables the CTA while quoting', () => {
    const answer = new Subject<Oferta>();
    const vm = filled(new CotizacionFormViewModel(() => answer));

    vm.quote();

    expect(vm.status()).toBe('quoting');
    expect(vm.canQuote()).toBeFalse();
    vm.quote();
    answer.next(OFERTA);
    expect(vm.status()).toBe('quoted');
  });

  it('degrades to no offer when a field changes after quoting', () => {
    const vm = filled(new CotizacionFormViewModel(() => of(OFERTA)));
    vm.quote();

    vm.edit('ciudad', 'cali');

    expect(vm.oferta()).toBeNull();
    expect(vm.status()).toBe('idle');
  });

  it('marks the field the core rejected and keeps it until edited (HU-3)', () => {
    const vm = filled(new CotizacionFormViewModel(() => throwError(fueraDeRango)));

    vm.quote();

    expect(vm.status()).toBe('rejected');
    expect(vm.rechazo()).toEqual(FUERA_DE_RANGO);
    expect(vm.issue('cilindraje_cc')).toBe('range');
    expect(vm.issue('modelo_anio')).toBeNull();
    expect(vm.oferta()).toBeNull();

    vm.edit('modelo_anio', '2023');
    expect(vm.issue('cilindraje_cc')).toBe('range');
    vm.edit('cilindraje_cc', '160');
    expect(vm.issue('cilindraje_cc')).toBeNull();
    expect(vm.rechazo()).toBeNull();
  });

  it('keeps a rejection that names no known field as a banner only', () => {
    const conflict = new HttpErrorResponse({ status: 409, error: null });
    const vm = filled(new CotizacionFormViewModel(() => throwError(() => conflict)));

    vm.quote();

    expect(vm.status()).toBe('rejected');
    expect(vm.rechazo()).toEqual({ codigo: 'rechazo', mensaje: '' });
    expect(vm.issue('cilindraje_cc')).toBeNull();
  });

  it('reports an outage as an error, not as invalid data', () => {
    const outage = new HttpErrorResponse({ status: 503 });
    const vm = filled(new CotizacionFormViewModel(() => throwError(() => outage)));

    vm.quote();

    expect(vm.status()).toBe('error');
    expect(vm.rechazo()).toBeNull();
  });
});
