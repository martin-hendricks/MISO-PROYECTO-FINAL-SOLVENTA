import { of, Subject, throwError } from 'rxjs';
import { Motivo, ResultadoEmision } from './emision.gateway';
import { EMITIDA, MOTIVO, RECHAZADA } from './emision.testing';
import { EmisionViewModel } from './emision.viewmodel';

describe('EmisionViewModel', () => {
  it('stays issuing until the core answers', () => {
    const pending = new Subject<ResultadoEmision>();
    const viewModel = new EmisionViewModel(
      () => pending,
      () => undefined,
    );

    viewModel.issue();

    expect(viewModel.status()).toBe('issuing');
    expect(viewModel.poliza()).toBeNull();
  });

  it('shows the issued policy', () => {
    const viewModel = new EmisionViewModel(
      () => of(EMITIDA),
      () => undefined,
    );

    viewModel.issue();

    expect(viewModel.status()).toBe('issued');
    expect(viewModel.poliza()?.numero).toBe('POL-2026-00088421');
  });

  it('hands the stored reason over when the core rejects', () => {
    const reasons: Motivo[] = [];
    const viewModel = new EmisionViewModel(
      () => of(RECHAZADA),
      (motivo) => reasons.push(motivo),
    );

    viewModel.issue();

    expect(viewModel.status()).toBe('rejected');
    expect(viewModel.poliza()).toBeNull();
    expect(reasons).toEqual([MOTIVO]);
  });

  it('recovers on retry after a failure', () => {
    let attempts = 0;
    const viewModel = new EmisionViewModel(
      () => (++attempts === 1 ? throwError(() => new Error('sin red')) : of(EMITIDA)),
      () => undefined,
    );

    viewModel.issue();
    expect(viewModel.status()).toBe('error');

    viewModel.issue();
    expect(viewModel.status()).toBe('issued');
  });
});
