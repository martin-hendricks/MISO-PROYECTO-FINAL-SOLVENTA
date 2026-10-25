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
