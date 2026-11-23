import { of, Subject, throwError } from 'rxjs';
import { AvisoPoliza } from '../polizas.gateway';
import { AVISOS } from '../polizas.testing';
import { PolizasAvisosViewModel } from './polizas-avisos.viewmodel';

describe('PolizasAvisosViewModel', () => {
  it('stays loading until the BFF answers', () => {
    const pending = new Subject<AvisoPoliza[]>();
    const viewModel = new PolizasAvisosViewModel(() => pending);

    viewModel.load();

    expect(viewModel.status()).toBe('loading');
    expect(viewModel.avisos()).toEqual([]);
  });

  it('lists the policies about to expire', () => {
    const viewModel = new PolizasAvisosViewModel(() => of(AVISOS));

    viewModel.load();

    expect(viewModel.status()).toBe('ready');
    expect(viewModel.avisos()).toEqual(AVISOS);
  });

  it('reports no policy about to expire', () => {
    const viewModel = new PolizasAvisosViewModel(() => of([]));

    viewModel.load();

    expect(viewModel.status()).toBe('empty');
  });

  it('recovers on retry after a failure', () => {
    let attempts = 0;
    const viewModel = new PolizasAvisosViewModel(() =>
      ++attempts === 1 ? throwError(() => new Error('sin red')) : of(AVISOS),
    );

    viewModel.load();
    expect(viewModel.status()).toBe('error');

    viewModel.load();
    expect(viewModel.status()).toBe('ready');
  });
});
