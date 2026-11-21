import { HttpErrorResponse } from '@angular/common/http';
import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import {
  Alcance,
  ALCANCES,
  CredencialEmitida,
  ListaSocios,
  Socio,
  SocioCreado,
  SocioNuevo,
} from './socios.gateway';

export type SociosStatus = 'loading' | 'ready' | 'empty' | 'error';

export const NOMBRE_MAXIMO = 120;

export interface PuertosSocios {
  listar: () => Observable<ListaSocios>;
  crear: (body: SocioNuevo) => Observable<SocioCreado>;
  rotar: (socioId: string) => Observable<CredencialEmitida>;
  revocarCredencial: (socioId: string, credencialId: string) => Observable<void>;
  revocar: (socioId: string) => Observable<Socio>;
}

export interface ClaveNueva {
  nombre: string;
  apiKey: string;
}

export type Confirmacion =
  | { tipo: 'credencial'; socioId: string; credencialId: string }
  | { tipo: 'socio'; socioId: string };

export class SociosViewModel {
  readonly status = signal<SociosStatus>('loading');
  readonly socios = signal<Socio[]>([]);
  readonly formularioAbierto = signal(false);
  readonly nombre = signal('');
  readonly alcances = signal<Alcance[]>([]);
  readonly guardando = signal(false);
  readonly mensaje = signal<string | null>(null);
  readonly claveNueva = signal<ClaveNueva | null>(null);
  readonly confirmando = signal<Confirmacion | null>(null);

  readonly puedeGuardar = computed(() => {
    const nombre = this.nombre().trim();
    return nombre.length > 0 && nombre.length <= NOMBRE_MAXIMO && this.alcances().length > 0;
  });

  constructor(private readonly puertos: PuertosSocios) {}

  cargar(): void {
    this.status.set('loading');
    this.puertos.listar().subscribe({
      next: (lista) => {
        this.socios.set(lista.socios);
        this.status.set(lista.socios.length ? 'ready' : 'empty');
      },
      error: () => this.status.set('error'),
    });
  }

  admiteAcciones(socio: Socio): boolean {
    return socio.estado === 'activo';
  }

  abrirCrear(): void {
    this.mensaje.set(null);
    this.nombre.set('');
    this.alcances.set([]);
    this.formularioAbierto.set(true);
  }

  cerrarFormulario(): void {
    this.formularioAbierto.set(false);
    this.mensaje.set(null);
  }

  editarNombre(valor: string): void {
    this.nombre.set(valor);
  }

  alternarAlcance(alcance: Alcance): void {
    this.alcances.update((actuales) =>
      actuales.includes(alcance)
        ? actuales.filter((actual) => actual !== alcance)
        : ALCANCES.filter((candidato) => candidato === alcance || actuales.includes(candidato)),
    );
  }

  guardar(): void {
    if (!this.puedeGuardar() || this.guardando()) {
      return;
    }
    this.guardando.set(true);
    this.mensaje.set(null);
    this.puertos.crear({ nombre: this.nombre().trim(), alcances: this.alcances() }).subscribe({
      next: (creado) => {
        this.guardando.set(false);
        this.formularioAbierto.set(false);
        this.claveNueva.set({ nombre: creado.nombre, apiKey: creado.apiKey });
        this.cargar();
      },
      error: (error: unknown) => this.fallo(error),
    });
  }

  rotar(socio: Socio): void {
    if (!this.admiteAcciones(socio)) {
      return;
    }
    this.mensaje.set(null);
    this.puertos.rotar(socio.socioId).subscribe({
      next: (emitida) => {
        this.claveNueva.set({ nombre: socio.nombre, apiKey: emitida.apiKey });
        this.cargar();
      },
      error: (error: unknown) => this.fallo(error),
    });
  }

  cerrarClave(): void {
    this.claveNueva.set(null);
  }

  pedirRevocarCredencial(socioId: string, credencialId: string): void {
    if (!this.activo(socioId)) {
      return;
    }
    this.confirmando.set({ tipo: 'credencial', socioId, credencialId });
  }

  pedirRevocarSocio(socioId: string): void {
    if (!this.activo(socioId)) {
      return;
    }
    this.confirmando.set({ tipo: 'socio', socioId });
  }

  cancelarConfirmacion(): void {
    this.confirmando.set(null);
  }

  confirmar(): void {
    const confirmacion = this.confirmando();
    if (!confirmacion) {
      return;
    }
    this.confirmando.set(null);
    this.mensaje.set(null);
    const pedido: Observable<unknown> =
      confirmacion.tipo === 'credencial'
        ? this.puertos.revocarCredencial(confirmacion.socioId, confirmacion.credencialId)
        : this.puertos.revocar(confirmacion.socioId);
    pedido.subscribe({
      next: () => this.cargar(),
      error: (error: unknown) => this.fallo(error),
    });
  }

  private activo(socioId: string): boolean {
    const socio = this.socios().find((candidato) => candidato.socioId === socioId);
    return socio !== undefined && this.admiteAcciones(socio);
  }

  private fallo(error: unknown): void {
    this.guardando.set(false);
    const mensaje =
      error instanceof HttpErrorResponse
        ? (error.error as { mensaje?: unknown } | null)?.mensaje
        : undefined;
    if (typeof mensaje === 'string' && mensaje) {
      this.mensaje.set(mensaje);
      return;
    }
    this.status.set('error');
  }
}
