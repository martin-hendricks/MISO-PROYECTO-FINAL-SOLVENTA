import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { Cliente } from './clientes.gateway';

export type ClientesStatus = 'loading' | 'ready' | 'empty' | 'error';

export class ClientesViewModel {
  private readonly statusState = signal<ClientesStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly clientesState = signal<Cliente[]>([]);
  readonly clientes = this.clientesState.asReadonly();

  readonly kpis = computed(() => {
    const clientes = this.clientesState();
    return {
      active: clientes.filter((cliente) => cliente.estado === 'activo').length,
      web: clientes.filter((cliente) => cliente.canal === 'web').length,
      android: clientes.filter((cliente) => cliente.canal === 'android').length,
      pendingConsent: clientes.filter(
        (cliente) => cliente.consentimiento === 'hipotecario_pendiente',
      ).length,
    };
  });

  constructor(private readonly source: () => Observable<Cliente[]>) {}

  load(): void {
    this.statusState.set('loading');
    this.source().subscribe({
      next: (clientes) => {
        this.clientesState.set(clientes);
        this.statusState.set(clientes.length ? 'ready' : 'empty');
      },
      error: () => this.statusState.set('error'),
    });
  }
}
