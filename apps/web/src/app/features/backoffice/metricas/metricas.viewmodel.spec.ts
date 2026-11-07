import { of, Subject, throwError } from 'rxjs';
import { Conteo } from './metricas.gateway';
import { MetricasViewModel } from './metricas.viewmodel';

const CONTEOS: Conteo[] = [
  { tipo: 'PolizaEmitida', fecha: '2026-10-01', cantidad: 3 },
  { tipo: 'PolizaCancelada', fecha: '2026-10-02', cantidad: 1 },
];

describe('MetricasViewModel', () => {
  it('stays loading until the backend answers', () => {
    const pending = new Subject<Conteo[]>();
    const viewModel = new MetricasViewModel(() => pending);

    viewModel.load('2026-10-01', '2026-10-31');

    expect(viewModel.status()).toBe('loading');
    expect(viewModel.conteos()).toEqual([]);
  });

  it('lists the aggregated counts', () => {
    const viewModel = new MetricasViewModel(() => of(CONTEOS));

    viewModel.load('2026-10-01', '2026-10-31');

    expect(viewModel.status()).toBe('ready');
    expect(viewModel.conteos()).toEqual(CONTEOS);
  });

  it('reports no event registered in the range', () => {
    const viewModel = new MetricasViewModel(() => of([]));

    viewModel.load('2026-10-01', '2026-10-31');

    expect(viewModel.status()).toBe('empty');
  });

  it('recovers on retry after a failure', () => {
    let attempts = 0;
    const viewModel = new MetricasViewModel(() =>
      ++attempts === 1 ? throwError(() => new Error('sin red')) : of(CONTEOS),
    );

    viewModel.load('2026-10-01', '2026-10-31');
    expect(viewModel.status()).toBe('error');

    viewModel.load('2026-10-01', '2026-10-31');
    expect(viewModel.status()).toBe('ready');
  });
});
