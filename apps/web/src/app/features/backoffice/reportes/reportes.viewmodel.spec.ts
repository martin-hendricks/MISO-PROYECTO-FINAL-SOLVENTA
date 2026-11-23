import { Observable, of, Subject, throwError } from 'rxjs';
import { ReporteGenerado } from './reportes.gateway';
import { ReportesViewModel } from './reportes.viewmodel';

const REPORTE: ReporteGenerado = {
  nombreArchivo: 'regulador_2026-10-01_2026-10-31.csv',
  tipoContenido: 'text/csv',
  contenido: 'numero,estado\nPOL-1,vigente\n',
};

function viewModel(
  regulador: (desde: string, hasta: string) => Observable<ReporteGenerado> = () => of(REPORTE),
  reaseguradora: (desde: string, hasta: string) => Observable<ReporteGenerado> = () => of(REPORTE),
) {
  return new ReportesViewModel(regulador, reaseguradora);
}

describe('ReportesViewModel', () => {
  it('starts idle for both reports', () => {
    const vm = viewModel();

    expect(vm.status()).toEqual({ regulador: 'idle', reaseguradora: 'idle' });
  });

  it('marks only the regulator report as generating while the BFF answers', () => {
    const pending = new Subject<ReporteGenerado>();
    const vm = viewModel(() => pending);

    vm.generar('regulador', '2026-10-01', '2026-10-31');

    expect(vm.status().regulador).toBe('generando');
    expect(vm.status().reaseguradora).toBe('idle');
  });

  it('stores the regulator report once ready', () => {
    const vm = viewModel();

    vm.generar('regulador', '2026-10-01', '2026-10-31');

    expect(vm.status().regulador).toBe('listo');
    expect(vm.reporte().regulador).toEqual(REPORTE);
    expect(vm.reporte().reaseguradora).toBeNull();
  });

  it('stores the reinsurer extract independently from the regulator one', () => {
    const vm = viewModel(
      () => of(REPORTE),
      () => of({ ...REPORTE, nombreArchivo: 'reaseguradora.csv' }),
    );

    vm.generar('reaseguradora', '2026-10-01', '2026-10-31');

    expect(vm.status().reaseguradora).toBe('listo');
    expect(vm.reporte().reaseguradora?.nombreArchivo).toBe('reaseguradora.csv');
    expect(vm.reporte().regulador).toBeNull();
  });

  it('reports a BFF failure as an error for that report only', () => {
    const vm = viewModel(() => throwError(() => new Error('boom')));

    vm.generar('regulador', '2026-10-01', '2026-10-31');

    expect(vm.status().regulador).toBe('error');
    expect(vm.reporte().regulador).toBeNull();
  });
});
