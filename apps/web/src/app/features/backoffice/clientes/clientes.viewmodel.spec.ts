import { of, Subject, throwError } from 'rxjs';
import { Cliente } from './clientes.gateway';
import { CLIENTES } from './clientes.testing';
import { ClientesViewModel } from './clientes.viewmodel';

describe('ClientesViewModel', () => {
  it('stays loading until the BFF answers', () => {
    const pending = new Subject<Cliente[]>();
    const viewModel = new ClientesViewModel(() => pending);

    viewModel.load();

    expect(viewModel.status()).toBe('loading');
    expect(viewModel.clientes()).toEqual([]);
  });

  it('lists the clients and counts the KPIs from them', () => {
    const viewModel = new ClientesViewModel(() => of(CLIENTES));

    viewModel.load();

    expect(viewModel.status()).toBe('ready');
    expect(viewModel.clientes().length).toBe(5);
    expect(viewModel.kpis()).toEqual({ active: 4, web: 3, android: 2, pendingConsent: 1 });
  });

  it('reports an empty portfolio', () => {
    const viewModel = new ClientesViewModel(() => of([]));

    viewModel.load();

    expect(viewModel.status()).toBe('empty');
    expect(viewModel.kpis()).toEqual({ active: 0, web: 0, android: 0, pendingConsent: 0 });
  });

  it('recovers on retry after a failure', () => {
    let attempts = 0;
    const viewModel = new ClientesViewModel(() =>
      ++attempts === 1 ? throwError(() => new Error('sin red')) : of(CLIENTES),
    );

    viewModel.load();
    expect(viewModel.status()).toBe('error');

    viewModel.load();
    expect(viewModel.status()).toBe('ready');
  });
});
