import { HttpErrorResponse } from '@angular/common/http';
import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import {
  Cliente,
  ClienteEdicion,
  ClienteNuevo,
  ConsultaClientes,
  EstadoCliente,
  FiltroEstado,
  PaginaClientes,
} from './clientes.gateway';

export type ClientesStatus = 'loading' | 'ready' | 'empty' | 'error';
export type Formulario = 'crear' | 'editar' | null;
export type PushEstado = 'si' | 'no' | 'desconocido';

export interface PuertosClientes {
  listar: (consulta: ConsultaClientes) => Observable<PaginaClientes>;
  crear: (body: ClienteNuevo) => Observable<Cliente>;
  editar: (usuarioId: string, body: ClienteEdicion) => Observable<Cliente>;
  cambiarEstado: (usuarioId: string, estado: EstadoCliente) => Observable<Cliente>;
}

export function pushDe(cliente: Cliente): PushEstado {
  if (cliente.dispositivosActivos === null) {
    return 'desconocido';
  }
  return cliente.dispositivosActivos > 0 ? 'si' : 'no';
}

export function nombreCliente(
  cliente: Pick<Cliente, 'nombre' | 'apellidos' | 'email'>,
): string {
  const nombre = [cliente.nombre, cliente.apellidos].filter((parte) => parte.trim()).join(' ');
  return nombre || cliente.email.trim();
}

function borradorVacio(): ClienteNuevo {
  return {
    tipoDocumento: 'CC',
    documento: '',
    email: '',
    password: '',
    nombre: '',
    apellidos: '',
  };
}

export class ClientesViewModel {
  readonly puedeEditar: boolean;
  readonly q = signal('');
  readonly estado = signal<FiltroEstado>('');
  readonly pagina = signal(1);
  readonly hayMas = signal(false);
  readonly status = signal<ClientesStatus>('loading');
  readonly clientes = signal<Cliente[]>([]);
  readonly formulario = signal<Formulario>(null);
  readonly editando = signal<string | null>(null);
  readonly borrador = signal<ClienteNuevo>(borradorVacio());
  readonly confirmando = signal<string | null>(null);
  readonly conflicto = signal<string | null>(null);
  readonly noEncontrado = signal(false);
  readonly guardando = signal(false);

  readonly puedeGuardar = computed(() => {
    const borrador = this.borrador();
    const comun =
      borrador.nombre.trim().length > 0 &&
      borrador.apellidos.trim().length > 0 &&
      borrador.email.trim().length > 0;
    if (this.formulario() !== 'crear') {
      return comun;
    }
    return (
      comun && borrador.documento.trim().length > 0 && borrador.password.trim().length > 0
    );
  });

  constructor(
    private readonly puertos: PuertosClientes,
    puedeEditar = false,
  ) {
    this.puedeEditar = puedeEditar;
  }

  cargar(): void {
    this.status.set('loading');
    this.puertos
      .listar({ q: this.q(), estado: this.estado(), pagina: this.pagina() })
      .subscribe({
        next: (pagina) => {
          this.clientes.set(pagina.clientes);
          this.pagina.set(pagina.pagina);
          this.hayMas.set(pagina.hayMas);
          this.status.set(pagina.clientes.length ? 'ready' : 'empty');
        },
        error: () => this.status.set('error'),
      });
  }

  buscar(texto: string): void {
    this.q.set(texto);
    this.pagina.set(1);
    this.cargar();
  }

  filtrar(estado: FiltroEstado): void {
    this.estado.set(estado);
    this.pagina.set(1);
    this.cargar();
  }

  siguiente(): void {
    if (!this.hayMas() || this.status() === 'loading') {
      return;
    }
    this.pagina.update((pagina) => pagina + 1);
    this.cargar();
  }

  anterior(): void {
    if (this.pagina() <= 1 || this.status() === 'loading') {
      return;
    }
    this.pagina.update((pagina) => pagina - 1);
    this.cargar();
  }

  abrirCrear(): void {
    if (!this.puedeEditar) {
      return;
    }
    this.conflicto.set(null);
    this.noEncontrado.set(false);
    this.editando.set(null);
    this.borrador.set(borradorVacio());
    this.formulario.set('crear');
  }

  abrirEditar(cliente: Cliente): void {
    if (!this.puedeEditar) {
      return;
    }
    this.conflicto.set(null);
    this.noEncontrado.set(false);
    this.editando.set(cliente.usuarioId);
    this.borrador.set({
      tipoDocumento: 'CC',
      documento: cliente.documento,
      email: cliente.email,
      password: '',
      nombre: cliente.nombre,
      apellidos: cliente.apellidos,
    });
    this.formulario.set('editar');
  }

  editarCampo(campo: keyof ClienteNuevo, valor: string): void {
    this.borrador.update((actual) => ({ ...actual, [campo]: valor }));
  }

  cerrarFormulario(): void {
    this.formulario.set(null);
    this.editando.set(null);
  }

  guardar(): void {
    if (!this.puedeEditar || !this.puedeGuardar() || this.guardando()) {
      return;
    }
    const borrador = this.borrador();
    this.guardando.set(true);
    this.conflicto.set(null);
    this.noEncontrado.set(false);
    const pedido =
      this.formulario() === 'editar' && this.editando()
        ? this.puertos.editar(this.editando()!, {
            nombre: borrador.nombre.trim(),
            apellidos: borrador.apellidos.trim(),
            email: borrador.email.trim(),
          })
        : this.puertos.crear({
            ...borrador,
            nombre: borrador.nombre.trim(),
            apellidos: borrador.apellidos.trim(),
            email: borrador.email.trim(),
            documento: borrador.documento.trim(),
            password: borrador.password,
            tipoDocumento: borrador.tipoDocumento.trim(),
          });
    pedido.subscribe({
      next: () => {
        this.guardando.set(false);
        this.cerrarFormulario();
        this.cargar();
      },
      error: (error: unknown) => this.fallo(error),
    });
  }

  pedirDesactivar(usuarioId: string): void {
    if (!this.puedeEditar) {
      return;
    }
    this.confirmando.set(usuarioId);
  }

  cancelarConfirmacion(): void {
    this.confirmando.set(null);
  }

  confirmarDesactivacion(): void {
    const usuarioId = this.confirmando();
    if (!usuarioId) {
      return;
    }
    this.confirmando.set(null);
    this.cambiar(usuarioId, 'INACTIVO');
  }

  reactivar(usuarioId: string): void {
    if (!this.puedeEditar) {
      return;
    }
    this.cambiar(usuarioId, 'ACTIVO');
  }

  private cambiar(usuarioId: string, estado: EstadoCliente): void {
    this.conflicto.set(null);
    this.noEncontrado.set(false);
    this.puertos.cambiarEstado(usuarioId, estado).subscribe({
      next: () => this.cargar(),
      error: (error: unknown) => this.fallo(error),
    });
  }

  private fallo(error: unknown): void {
    this.guardando.set(false);
    if (error instanceof HttpErrorResponse && error.status === 409) {
      this.conflicto.set((error.error as { mensaje?: string } | null)?.mensaje ?? '');
      return;
    }
    if (error instanceof HttpErrorResponse && error.status === 404) {
      this.noEncontrado.set(true);
      return;
    }
    this.status.set('error');
  }
}
