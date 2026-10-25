import { of, Subject, throwError } from 'rxjs';
import { PolizaDetalle } from '../polizas.gateway';
import { DETALLE } from '../polizas.testing';
import { PolizaDetalleViewModel } from './poliza-detalle.viewmodel';

describe('PolizaDetalleViewModel', () => {
  it('stays loading until the BFF answers', () => {
    const pending = new Subject<PolizaDetalle | null>();
    const viewModel = new PolizaDetalleViewModel(() => pending);

    viewModel.load();

    expect(viewModel.status()).toBe('loading');
    expect(viewModel.poliza()).toBeNull();
  });

  it('shows the policy the BFF returns', () => {
    const viewModel = new PolizaDetalleViewModel(() => of(DETALLE));

    viewModel.load();

    expect(viewModel.status()).toBe('ready');
    expect(viewModel.poliza()).toEqual(DETALLE);
  });

  it('reports a missing policy as not found', () => {
    const viewModel = new PolizaDetalleViewModel(() => of(null));

    viewModel.load();

    expect(viewModel.status()).toBe('not-found');
    expect(viewModel.poliza()).toBeNull();
  });

  it('recovers on retry after a failure', () => {
    let attempts = 0;
    const viewModel = new PolizaDetalleViewModel(() =>
      ++attempts === 1 ? throwError(() => new Error('sin red')) : of(DETALLE),
    );

    viewModel.load();
    expect(viewModel.status()).toBe('error');

    viewModel.load();
    expect(viewModel.status()).toBe('ready');
  });
});
