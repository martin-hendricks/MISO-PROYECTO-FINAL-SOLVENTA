import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { CiudadMapa } from '../../../prestadores/prestadores.gateway';
import { Pais } from '../../../prestadores/tipo-prestador';
import {
  EstadoPrestador,
  FiltroOperador,
  ListadoOperador,
  PrestadorOperador,
} from '../bo-prestadores.gateway';

export interface PuertosLista {
  listar: (filtro: FiltroOperador) => Observable<ListadoOperador>;
  ciudades: (pais: Pais) => Observable<CiudadMapa[]>;
  cambiarEstado: (id: string, estado: EstadoPrestador) => Observable<PrestadorOperador>;
}

export class BoPrestadoresListaViewModel {
  readonly status = signal<'loading' | 'ready' | 'empty' | 'error'>('loading');
  readonly prestadores = signal<PrestadorOperador[]>([]);
  readonly conteos = signal<Record<string, number>>({});
  readonly centro = signal<{ lat: number; lng: number } | null>(null);
  readonly ciudades = signal<CiudadMapa[]>([]);
  readonly pais = signal<Pais>('CO');
  readonly ramo = signal('');
  readonly ciudad = signal('');
  readonly estado = signal<'' | EstadoPrestador>('');
  readonly confirmando = signal<PrestadorOperador | null>(null);
  readonly errorAccion = signal(false);

  /** Catalog order, so cities without providers still read 0. */
  readonly resumenConteos = computed(() =>
    this.ciudades()
      .map((ciudad) => `${ciudad.nombre} ${this.conteos()[ciudad.nombre] ?? 0}`)
      .join(' · '),
  );

  readonly centroMapa = computed(() => {
    const primero = this.prestadores()[0] ?? this.ciudades()[0];
    return this.centro() ?? (primero ? { lat: primero.lat, lng: primero.lng } : null);
  });

  private ticketCiudades = 0;

  constructor(
    private readonly puertos: PuertosLista,
    readonly canWrite: boolean,
    pais: Pais,
  ) {
    this.pais.set(pais);
  }

  iniciar(): void {
    this.cargarCiudades();
    this.cargar();
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

  filtrarPais(pais: Pais): void {
    this.pais.set(pais);
    this.ciudad.set('');
    this.iniciar();
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

  private cargarCiudades(): void {
    const ticket = ++this.ticketCiudades;
    this.ciudades.set([]);
    this.puertos.ciudades(this.pais()).subscribe({
      next: (ciudades) => {
        if (ticket === this.ticketCiudades) {
          this.ciudades.set(ciudades);
        }
      },
      error: () => undefined,
    });
  }

  private consulta(): FiltroOperador {
    const ramo = this.ramo();
    const ciudad = this.ciudad();
    const estado = this.estado();
    return {
      pais: this.pais(),
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
