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
});
