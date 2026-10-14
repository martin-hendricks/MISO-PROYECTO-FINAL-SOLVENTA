import { Observable, of, Subject, throwError } from 'rxjs';
import { Oferta, SolicitudCotizacion } from './cotizacion.gateway';
import { FORMULARIO, OFERTA } from './cotizacion.testing';
import { CotizacionViewModel, Quotes } from './cotizacion.viewmodel';

describe('CotizacionViewModel', () => {
  function quotesAnswering(answer: () => Observable<Oferta>) {
    const quoted: SolicitudCotizacion[] = [];
    const found: string[] = [];
    const quotes: Quotes = {
      quote: (solicitud) => {
        quoted.push(solicitud);
        return answer();
      },
      find: (cotizacionId) => {
        found.push(cotizacionId);
        return answer();
      },
    };
    return { quotes, quoted, found };
  }

  it('keeps Calcular prima off until the form is complete', () => {
    const viewModel = new CotizacionViewModel(quotesAnswering(() => of(OFERTA)).quotes);

    expect(viewModel.canCalculate()).toBeFalse();
    viewModel.patch({ ...FORMULARIO, modelo: ' ' });
    expect(viewModel.canCalculate()).toBeFalse();
    viewModel.patch({ modelo: 'Galaxy A54' });
    expect(viewModel.canCalculate()).toBeTrue();
  });

  it('prices the risk on behalf of a third party and shows the firm offer', () => {
    const { quotes, quoted } = quotesAnswering(() => of(OFERTA));
    const viewModel = new CotizacionViewModel(quotes);
    viewModel.patch({ ...FORMULARIO, nombre: ' Andrés Gómez Molina ' });

    viewModel.calculate();

    expect(quoted).toEqual([
      {
        cliente: { nombre: 'Andrés Gómez Molina', documento: '1020334556' },
        ramo: 'dispositivo',
        vigenciaMeses: 12,
        datosRiesgo: {
          tipo: 'telefono',
          valorAsegurado: 1200000,
          marca: 'Samsung',
          modelo: 'Galaxy A54',
        },
      },
    ]);
    expect(viewModel.status()).toBe('ready');
    expect(viewModel.offer()).toEqual(OFERTA);
    expect(viewModel.canIssue()).toBeTrue();
  });

  it('reads the same quote by id instead of pricing it again', () => {
    const { quotes, quoted, found } = quotesAnswering(() => of(OFERTA));
    const viewModel = new CotizacionViewModel(quotes);
    viewModel.patch(FORMULARIO);

    viewModel.calculate();
    viewModel.calculate();

    expect(quoted.length).toBe(1);
    expect(found).toEqual(['COT-1042']);
    expect(viewModel.offer()).toEqual(OFERTA);
  });

  it('prices a new quote once the form changes', () => {
    const { quotes, quoted, found } = quotesAnswering(() => of(OFERTA));
    const viewModel = new CotizacionViewModel(quotes);
    viewModel.patch(FORMULARIO);
    viewModel.calculate();

    viewModel.patch({ marca: 'Motorola' });
    expect(viewModel.offer()).toBeNull();
    expect(viewModel.status()).toBe('idle');
    viewModel.calculate();

    expect(quoted.length).toBe(2);
    expect(found).toEqual([]);
  });

  it('flags an insured value outside the range without asking the BFF', () => {
    const { quotes, quoted } = quotesAnswering(() => of(OFERTA));
    const viewModel = new CotizacionViewModel(quotes);
    viewModel.patch(FORMULARIO);

    for (const valorAsegurado of ['0', '199999', '8000001', '1200000.5', 'mucho']) {
      viewModel.patch({ valorAsegurado });
      expect(viewModel.valorOutOfRange()).withContext(valorAsegurado).toBeTrue();
      expect(viewModel.canCalculate()).withContext(valorAsegurado).toBeFalse();
    }
    viewModel.calculate();
    expect(quoted).toEqual([]);

    for (const valorAsegurado of ['200000', '8000000']) {
      viewModel.patch({ valorAsegurado });
      expect(viewModel.valorOutOfRange()).withContext(valorAsegurado).toBeFalse();
    }
    expect(viewModel.form().nombre).toBe(FORMULARIO.nombre);
  });

  it('does not flag an insured value that is still empty', () => {
    const viewModel = new CotizacionViewModel(quotesAnswering(() => of(OFERTA)).quotes);

    viewModel.patch({ ...FORMULARIO, valorAsegurado: '' });

    expect(viewModel.valorOutOfRange()).toBeFalse();
    expect(viewModel.canCalculate()).toBeFalse();
  });

  it('holds the form while the BFF answers', () => {
    const pending = new Subject<Oferta>();
    const viewModel = new CotizacionViewModel(quotesAnswering(() => pending).quotes);
    viewModel.patch(FORMULARIO);

    viewModel.calculate();
    viewModel.patch({ marca: 'Motorola' });

    expect(viewModel.status()).toBe('submitting');
    expect(viewModel.canCalculate()).toBeFalse();
    expect(viewModel.form().marca).toBe('Samsung');

    pending.next(OFERTA);
    expect(viewModel.status()).toBe('ready');
  });

  it('keeps what was typed when pricing fails and recovers on retry', () => {
    let attempts = 0;
    const { quotes } = quotesAnswering(() =>
      ++attempts === 1 ? throwError(() => new Error('sin red')) : of(OFERTA),
    );
    const viewModel = new CotizacionViewModel(quotes);
    viewModel.patch(FORMULARIO);

    viewModel.calculate();
    expect(viewModel.status()).toBe('error');
    expect(viewModel.offer()).toBeNull();
    expect(viewModel.form()).toEqual(FORMULARIO);

    viewModel.calculate();
    expect(viewModel.status()).toBe('ready');
  });

  it('does not continue to issuance with an offer that is no longer in force', () => {
    const { quotes } = quotesAnswering(() => of({ ...OFERTA, estado: 'oferta_vencida' }));
    const viewModel = new CotizacionViewModel(quotes);
    viewModel.patch(FORMULARIO);

    expect(viewModel.canIssue()).toBeFalse();
    viewModel.calculate();

    expect(viewModel.offer()).not.toBeNull();
    expect(viewModel.canIssue()).toBeFalse();
  });

  it('clears the form and the offer', () => {
    const viewModel = new CotizacionViewModel(quotesAnswering(() => of(OFERTA)).quotes);
    viewModel.patch({ ...FORMULARIO, vigenciaMeses: 24 });
    viewModel.calculate();

    viewModel.clear();

    expect(viewModel.offer()).toBeNull();
    expect(viewModel.status()).toBe('idle');
    expect(viewModel.form().nombre).toBe('');
    expect(viewModel.form().vigenciaMeses).toBe(12);
  });
});
