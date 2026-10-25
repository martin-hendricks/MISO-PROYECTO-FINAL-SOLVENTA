import { HttpErrorResponse } from '@angular/common/http';
import { Observable, of, Subject, throwError } from 'rxjs';
import { CotizacionFormViewModel } from './cotizacion-form.viewmodel';
import { Catalogo, Oferta } from './cotizacion.gateway';
import {
  CATALOGO_DISPOSITIVO,
  CATALOGO_SOAT,
  FUERA_DE_RANGO,
  fueraDeRango,
  OFERTA,
} from './cotizacion.testing';
import { DatosRiesgo } from './ramos';

describe('CotizacionFormViewModel', () => {
  const CATALOGOS: Record<string, Catalogo> = {
    'Protección de dispositivo': CATALOGO_DISPOSITIVO,
    'SOAT motocicleta': CATALOGO_SOAT,
  };

  function form(
    source: (ramo: string, datos: DatosRiesgo) => Observable<Oferta> = () => of(OFERTA),
    onQuoted?: (oferta: Oferta) => void,
    catalog: (ramo: string) => Observable<Catalogo> = (ramo) => of(CATALOGOS[ramo]),
  ) {
    const vm = new CotizacionFormViewModel(catalog, source, onQuoted);
    vm.loadCatalog();
    return vm;
  }

  function dispositivo(vm: CotizacionFormViewModel) {
    vm.edit('valorDispositivo', '2400000');
    vm.edit('marca', 'apple');
    vm.edit('modelo', ' iPhone 15 ');
    vm.edit('masDe12Meses', 'no');
    return vm;
  }

  it('starts on Protección de dispositivo and lists the seven lines', () => {
    const vm = form();

    expect(vm.ramo().ramo).toBe('Protección de dispositivo');
    expect(vm.ramos.map((ramo) => [ramo.ramo, ramo.disponible])).toEqual([
      ['Protección de dispositivo', true],
      ['SOAT motocicleta', true],
      ['Microseguro de vida', false],
      ['Clima y vuelos', false],
      ['Vida hipotecario', false],
      ['Pagos', false],
      ['Viaje', false],
    ]);
  });

  it('sends the line and its risk data with the keys mobile uses', () => {
    const source = jasmine.createSpy('source').and.returnValue(of(OFERTA));
    const onQuoted = jasmine.createSpy('onQuoted');
    const vm = dispositivo(form(source, onQuoted));

    vm.quote();

    expect(source).toHaveBeenCalledOnceWith('Protección de dispositivo', {
      valorDispositivo: 2400000,
      marca: 'apple',
      modelo: 'iPhone 15',
      masDe12Meses: false,
    });
    expect(vm.status()).toBe('quoted');
    expect(onQuoted).toHaveBeenCalledOnceWith(OFERTA);
  });

  it('works without a quoted callback', () => {
    const vm = dispositivo(
      new CotizacionFormViewModel(
        (r) => of(CATALOGOS[r]),
        () => of(OFERTA),
      ),
    );
    vm.loadCatalog();

    vm.quote();

    expect(vm.status()).toBe('quoted');
  });

  it('reads coverages, ranges and options from the catalog of the line', () => {
    const vm = form();

    expect(vm.coberturas().map((c) => c.nombre)).toEqual([
      'Robo',
      'Daño accidental',
      'Reposición por equipo nuevo',
    ]);
    expect(vm.rangos()['valorDispositivo']).toEqual({ minimo: 500000, maximo: 10000000 });
    expect(vm.opciones('marca')).toEqual(['samsung', 'apple', 'xiaomi', 'motorola']);
    expect(vm.opciones('modelo')).toEqual([]);
  });

  it('blocks the quote while the insured value is out of range', () => {
    const source = jasmine.createSpy('source');
    const vm = dispositivo(form(source));

    vm.edit('valorDispositivo', '20000000');
    vm.quote();

    expect(vm.issue('valorDispositivo')).toBe('range');
    expect(vm.canQuote()).toBeFalse();
    expect(source).not.toHaveBeenCalled();
    expect(vm.valor('valorDispositivo')).toBe('20000000');
  });

  it('asks for positive integers, a catalog option and every field', () => {
    const vm = form();

    expect(vm.issue('modelo')).toBeNull();
    vm.touch('modelo');
    expect(vm.issue('modelo')).toBe('required');
    vm.edit('valorDispositivo', '-5');
    expect(vm.issue('valorDispositivo')).toBe('positive');
    vm.edit('valorDispositivo', '1.5');
    expect(vm.issue('valorDispositivo')).toBe('positive');
    vm.edit('marca', 'nokia');
    expect(vm.issue('marca')).toBe('option');
    vm.edit('masDe12Meses', 'si');
    expect(vm.issue('masDe12Meses')).toBeNull();
    expect(vm.canQuote()).toBeFalse();
  });

  it('switches line, reloads its catalog and clears the risk data', () => {
    const catalog = jasmine
      .createSpy('catalog')
      .and.callFake((ramo: string) => of(CATALOGOS[ramo]));
    const source = jasmine.createSpy('source').and.returnValue(of(OFERTA));
    const vm = dispositivo(form(source, undefined, catalog));
    vm.quote();

    vm.select('soat');

    expect(catalog.calls.mostRecent().args).toEqual(['SOAT motocicleta']);
    expect(vm.ramo().id).toBe('soat');
    expect(vm.valor('valorDispositivo')).toBe('');
    expect(vm.oferta()).toBeNull();
    vm.edit('cilindraje_cc', '150');
    vm.edit('modelo_anio', '2022');
    vm.edit('ciudad_circulacion', 'cali');
    vm.quote();
    expect(source.calls.mostRecent().args).toEqual([
      'SOAT motocicleta',
      { cilindraje_cc: 150, modelo_anio: 2022, ciudad_circulacion: 'cali' },
    ]);
  });

  it('ignores an unknown line or one that does not quote yet', () => {
    const vm = form();

    vm.select('viaje');
    vm.select('hogar');

    expect(vm.ramo().id).toBe('dispositivo');
  });

  it('blocks the CTA until the catalog loads and when it fails', () => {
    const catalogo = new Subject<Catalogo>();
    let fail = false;
    const vm = dispositivo(
      form(undefined, undefined, () =>
        fail ? throwError(() => new HttpErrorResponse({ status: 503 })) : catalogo,
      ),
    );

    expect(vm.catalogoStatus()).toBe('loading');
    expect(vm.moneda()).toBe('COP');
    expect(vm.canQuote()).toBeFalse();
    catalogo.next({ ...CATALOGO_DISPOSITIVO, moneda: 'PEN' });
    expect(vm.moneda()).toBe('PEN');
    expect(vm.canQuote()).toBeTrue();

    fail = true;
    vm.loadCatalog();
    expect(vm.catalogoStatus()).toBe('error');
    expect(vm.canQuote()).toBeFalse();
  });

  it('leaves a value without a catalog range to the core', () => {
    const vm = form(undefined, undefined, () =>
      of({ ...CATALOGO_DISPOSITIVO, datosRiesgo: [], coberturas: [] }),
    );

    vm.edit('valorDispositivo', '99999999');

    expect(vm.issue('valorDispositivo')).toBeNull();
    expect(vm.coberturas()).toEqual([]);
  });

  it('disables the CTA while quoting', () => {
    const answer = new Subject<Oferta>();
    const vm = dispositivo(form(() => answer));

    vm.quote();

    expect(vm.status()).toBe('quoting');
    expect(vm.canQuote()).toBeFalse();
    vm.quote();
    answer.next(OFERTA);
    expect(vm.status()).toBe('quoted');
  });

  it('degrades to no offer when a field changes after quoting', () => {
    const vm = dispositivo(form());
    vm.quote();

    vm.edit('modelo', 'iPhone 14');

    expect(vm.oferta()).toBeNull();
    expect(vm.status()).toBe('idle');
  });

  it('marks the field the core rejected and keeps it until edited (HU-3)', () => {
    const vm = dispositivo(form(() => throwError(fueraDeRango)));

    vm.quote();

    expect(vm.status()).toBe('rejected');
    expect(vm.rechazo()).toEqual(FUERA_DE_RANGO);
    expect(vm.issue('valorDispositivo')).toBe('range');
    vm.edit('modelo', 'iPhone 14');
    expect(vm.issue('valorDispositivo')).toBe('range');
    vm.edit('valorDispositivo', '2500000');
    expect(vm.issue('valorDispositivo')).toBeNull();
    expect(vm.rechazo()).toBeNull();
  });

  it('keeps a rejection that names no field of the line as a banner only', () => {
    const conflict = new HttpErrorResponse({ status: 409, error: null });
    const vm = dispositivo(form(() => throwError(() => conflict)));

    vm.quote();

    expect(vm.status()).toBe('rejected');
    expect(vm.rechazo()).toEqual({ codigo: 'rechazo', mensaje: '' });
    expect(vm.issue('valorDispositivo')).toBeNull();
  });

  it('reports an outage as an error, not as invalid data', () => {
    const outage = new HttpErrorResponse({ status: 503 });
    const vm = dispositivo(form(() => throwError(() => outage)));

    vm.quote();

    expect(vm.status()).toBe('error');
    expect(vm.rechazo()).toBeNull();
  });
});
