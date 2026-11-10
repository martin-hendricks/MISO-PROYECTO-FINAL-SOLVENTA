import { of, Subject, throwError } from 'rxjs';
import { Inicio } from './inicio.gateway';
import { INICIO, INICIO_VACIO } from './inicio.testing';
import { InicioViewModel } from './inicio.viewmodel';

describe('InicioViewModel', () => {
  it('stays loading without cards until the BFF answers', () => {
    const pending = new Subject<Inicio>();
    const viewModel = new InicioViewModel(() => pending);

    viewModel.load();

    expect(viewModel.status()).toBe('loading');
    expect(viewModel.panel()).toEqual({
      offer: null,
      policy: null,
      claim: null,
      vidaCrediticia: false,
    });
  });

  it('draws every card the aggregate brings', () => {
    const viewModel = new InicioViewModel(() => of(INICIO));

    viewModel.load();

    expect(viewModel.status()).toBe('ready');
    expect(viewModel.panel()).toEqual({
      offer: INICIO.ofertaVigente,
      policy: INICIO.poliza,
      claim: INICIO.siniestroEnCurso,
      vidaCrediticia: true,
    });
  });

  it('keeps each card independent of the others', () => {
    const viewModel = new InicioViewModel(() =>
      of({ ...INICIO_VACIO, siniestroEnCurso: INICIO.siniestroEnCurso }),
    );

    viewModel.load();

    expect(viewModel.status()).toBe('ready');
    expect(viewModel.panel().claim?.siniestroId).toBe('SIN-441');
    expect(viewModel.panel().offer).toBeNull();
    expect(viewModel.panel().policy).toBeNull();
    expect(viewModel.panel().vidaCrediticia).toBeFalse();
  });

  it('hides an offer that has already expired', () => {
    const viewModel = new InicioViewModel(
      () => of({ ...INICIO, ofertaVigente: { ...INICIO.ofertaVigente!, venceEn: '2000-01-01T00:00:00Z' } }),
      () => new Date('2026-06-01T12:00:00Z'),
    );

    viewModel.load();

    expect(viewModel.panel().offer).toBeNull();
    expect(viewModel.panel().policy?.numero).toBe('POL-88219-CO');
  });

  it('drops an offer without a quote that can be consulted again', () => {
    const viewModel = new InicioViewModel(() =>
      of({ ...INICIO, ofertaVigente: { ...INICIO.ofertaVigente!, cotizacionId: '' } }),
    );

    viewModel.load();

    expect(viewModel.panel().offer).toBeNull();
  });

  it('links only a policy in force', () => {
    const viewModel = new InicioViewModel(() =>
      of({ ...INICIO_VACIO, poliza: { ...INICIO.poliza!, estado: 'cancelada' } }),
    );

    viewModel.load();

    expect(viewModel.panel().policy).toBeNull();
    expect(viewModel.status()).toBe('empty');
  });

  it('reports a home with no cards', () => {
    const viewModel = new InicioViewModel(() => of(INICIO_VACIO));

    viewModel.load();

    expect(viewModel.status()).toBe('empty');
  });

  it('shows the wallet link only when there is a deposit', () => {
    const withDeposit = new InicioViewModel(
      () => of(INICIO),
      () => new Date(),
      () => of({ movimientos: [{}] }),
    );
    withDeposit.load();
    expect(withDeposit.deposits()).toBe(1);

    const failed = new InicioViewModel(
      () => of(INICIO),
      () => new Date(),
      () => throwError(() => new Error('caido')),
    );
    failed.load();
    expect(failed.deposits()).toBe(0);
    expect(failed.status()).toBe('ready');
  });

  it('recovers on retry after a failure', () => {
    let attempts = 0;
    const viewModel = new InicioViewModel(() =>
      ++attempts === 1 ? throwError(() => new Error('sin red')) : of(INICIO),
    );

    viewModel.load();
    expect(viewModel.status()).toBe('error');

    viewModel.load();
    expect(viewModel.status()).toBe('ready');
  });
});
