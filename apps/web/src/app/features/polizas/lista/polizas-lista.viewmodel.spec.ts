import { of, Subject, throwError } from 'rxjs';
import { PolizaResumen } from '../polizas.gateway';
import { POLIZAS } from '../polizas.testing';
import { PolizasListaViewModel } from './polizas-lista.viewmodel';

describe('PolizasListaViewModel', () => {
  it('stays loading until the BFF answers', () => {
    const pending = new Subject<PolizaResumen[]>();
    const viewModel = new PolizasListaViewModel(() => pending);

    viewModel.load();

    expect(viewModel.status()).toBe('loading');
    expect(viewModel.polizas()).toEqual([]);
  });

  it('lists the customer policies', () => {
    const viewModel = new PolizasListaViewModel(() => of(POLIZAS));

    viewModel.load();

    expect(viewModel.status()).toBe('ready');
    expect(viewModel.polizas()).toEqual(POLIZAS);
  });

  it('reports an empty wallet', () => {
    const viewModel = new PolizasListaViewModel(() => of([]));

    viewModel.load();

    expect(viewModel.status()).toBe('empty');
  });

  it('recovers on retry after a failure', () => {
    let attempts = 0;
    const viewModel = new PolizasListaViewModel(() =>
      ++attempts === 1 ? throwError(() => new Error('sin red')) : of(POLIZAS),
    );

    viewModel.load();
    expect(viewModel.status()).toBe('error');

    viewModel.load();
    expect(viewModel.status()).toBe('ready');
  });
});
