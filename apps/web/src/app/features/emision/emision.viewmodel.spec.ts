import { HttpErrorResponse } from '@angular/common/http';
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
    viewModel.chooseRenewal(true);
    expect(viewModel.renewal()).toBeTrue();
  });

  it('keeps renewal off until the customer changes it, without another issuance', () => {
    const issued = of(EMITIDA);
    const saved: boolean[] = [];
    const vm = new EmisionViewModel(
      () => issued,
      () => fail('should not reject'),
      (_numero, enabled) => {
        saved.push(enabled);
        return of({ numero: 'POL-2026-00088421', renovacionAutomatica: enabled });
      },
    );
    vm.issue();
    expect(vm.status()).toBe('issued');
    expect(vm.renewal()).toBeFalse();
    expect(saved).toEqual([]);
    vm.chooseRenewal(true);
    expect(saved).toEqual([true]);
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
    viewModel.chooseRenewal(true);
    expect(viewModel.renewal()).toBeFalse();
  });

  it('maps a race-time expired offer to a new quotation', () => {
    const viewModel = new EmisionViewModel(
      () =>
        throwError(
          () => new HttpErrorResponse({ status: 409, error: { codigo: 'oferta_vencida' } }),
        ),
      () => undefined,
    );

    viewModel.issue();

    expect(viewModel.status()).toBe('expired');
    expect(viewModel.poliza()).toBeNull();
  });

  it('maps a revoked profiling consent to a new quotation', () => {
    const viewModel = new EmisionViewModel(
      () =>
        throwError(
          () => new HttpErrorResponse({ status: 422, error: { codigo: 'consentimiento_revocado' } }),
        ),
      () => undefined,
    );

    viewModel.issue();

    expect(viewModel.status()).toBe('revoked');
    expect(viewModel.poliza()).toBeNull();
  });

  it('keeps other 422 rejections as a retryable error', () => {
    const viewModel = new EmisionViewModel(
      () => throwError(() => new HttpErrorResponse({ status: 422, error: { codigo: 'oferta_ya_usada' } })),
      () => undefined,
    );

    viewModel.issue();

    expect(viewModel.status()).toBe('error');
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
