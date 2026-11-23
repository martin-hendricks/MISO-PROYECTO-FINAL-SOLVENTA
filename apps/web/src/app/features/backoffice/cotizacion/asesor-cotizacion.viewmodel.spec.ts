import { of } from 'rxjs';
import { AsesorCotizacionViewModel } from './asesor-cotizacion.viewmodel';

describe('AsesorCotizacionViewModel', () => {
  it('keeps COP when the caller does not pass a region currency', () => {
    const vm = new AsesorCotizacionViewModel(
      () => of(),
      () => of(),
      () => of(),
    );

    expect(vm.form.moneda()).toBe('COP');
  });

  it('has no customer reference and finds nobody when no client search is wired', () => {
    const vm = new AsesorCotizacionViewModel(
      () => of(),
      () => of(),
      () => of(),
    );

    vm.buscar('Andrés');

    expect(vm.clienteRef()).toBe('');
    expect(vm.resultados()).toEqual([]);
    expect(vm.sinResultados()).toBeTrue();
  });
});
