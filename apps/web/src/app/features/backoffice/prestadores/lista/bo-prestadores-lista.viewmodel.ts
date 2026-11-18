import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import {
  EstadoPrestador,
  FiltroOperador,
  ListadoOperador,
  PrestadorOperador,
} from '../bo-prestadores.gateway';

export interface PuertosLista {
  listar: (filtro: FiltroOperador) => Observable<ListadoOperador>;
  cambiarEstado: (id: string, estado: EstadoPrestador) => Observable<PrestadorOperador>;
}

export class BoPrestadoresListaViewModel {
  readonly status = signal<'loading' | 'ready' | 'empty' | 'error'>('loading');
  readonly prestadores = signal<PrestadorOperador[]>([]);
  readonly conteos = signal({ Bogotá: 0, Medellín: 0, Chía: 0 });
  readonly centro = signal<{ lat: number; lng: number } | null>(null);
  readonly ramo = signal('');
  readonly ciudad = signal('');
  readonly estado = signal<'' | EstadoPrestador>('');
  readonly confirmando = signal<PrestadorOperador | null>(null);
  readonly errorAccion = signal(false);

  constructor(
    private readonly puertos: PuertosLista,
    readonly canWrite: boolean,
  ) {}

  bogota(): number {
    return this.conteos().Bogotá;
  }

  medellin(): number {
    return this.conteos().Medellín;
  }

  chia(): number {
    return this.conteos().Chía;
  }

  cargar(): void {
    this.status.set('loading');
    this.puertos.listar(this.consulta()).subscribe({
      next: (pagina) => {
        this.conteos.set(pagina.conteos);
        this.centro.set(pagina.centro);
        this.prestadores.set(pagina.prestadores);
        this.status.set(pagina.prestadores.length ? 'ready' : 'empty');
      },
      error: () => {
        this.prestadores.set([]);
        this.status.set('error');
      },
    });
  }

  filtrarRamo(ramo: string): void {
    this.ramo.set(ramo);
    this.cargar();
  }

  filtrarCiudad(ciudad: string): void {
    this.ciudad.set(ciudad);
    this.cargar();
  }

  filtrarEstado(estado: '' | EstadoPrestador): void {
    this.estado.set(estado);
    this.cargar();
  }

  quitarFiltros(): void {
    this.ramo.set('');
    this.ciudad.set('');
    this.estado.set('');
    this.cargar();
  }

  pedirInactivar(prestador: PrestadorOperador): void {
    if (!this.canWrite) {
      return;
    }
    this.confirmando.set(prestador);
  }

  cancelarConfirmacion(): void {
    this.confirmando.set(null);
  }

  confirmarInactivar(): void {
    const prestador = this.confirmando();
    if (!prestador) {
      return;
    }
    this.confirmar(prestador.id, 'inactivo');
  }

  reactivar(prestador: PrestadorOperador): void {
    if (!this.canWrite) {
      return;
    }
    this.confirmar(prestador.id, 'activo');
  }

  private consulta(): FiltroOperador {
    const ramo = this.ramo();
    const ciudad = this.ciudad();
    const estado = this.estado();
    return {
      ...(ramo ? { ramo } : {}),
      ...(ciudad ? { ciudad } : {}),
      ...(estado ? { estado } : {}),
    };
  }

  private confirmar(id: string, estado: EstadoPrestador): void {
    this.errorAccion.set(false);
    this.puertos.cambiarEstado(id, estado).subscribe({
      next: (actualizado) => {
        this.confirmando.set(null);
        this.prestadores.update((filas) =>
          filas.map((fila) => (fila.id === actualizado.id ? actualizado : fila)),
        );
      },
      error: () => this.errorAccion.set(true),
    });
  }
}
