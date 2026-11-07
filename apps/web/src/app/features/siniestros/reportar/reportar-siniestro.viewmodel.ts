import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { PolizaResumen } from '../../polizas/polizas.gateway';
import { AvisoRecibido, esRechazoAviso, NuevoAviso, Ubicacion } from '../siniestros.gateway';

export type Paso = 'formulario' | 'evidencia' | 'enviado';
export type PolizasStatus = 'loading' | 'ready' | 'sin-polizas' | 'error';
export type UbicacionStatus = 'pendiente' | 'solicitando' | 'guardada' | 'bloqueada';
export type EnvioStatus = 'idle' | 'enviando' | 'error' | 'rechazado';

/** Mismos límites que valida el núcleo (Figma evidencia-siniestro: PNG, JPG o PDF, 10 MB). */
export const TIPOS_PERMITIDOS = ['image/png', 'image/jpeg', 'application/pdf'];
export const TAMANO_MAXIMO = 10 * 1024 * 1024;

export interface Dependencias {
  polizas: () => Observable<PolizaResumen[]>;
  enviar: (aviso: NuevoAviso, clave: string) => Observable<AvisoRecibido>;
  /** Ubicación del navegador; rechaza si el usuario bloquea o no hay geolocalización. */
  ubicar: () => Promise<Ubicacion>;
  hoy: () => string;
  nuevaClave: () => string;
}

/** HU-116 (formulario) -> HU-100 (evidencia + geo opcional) -> HU-110 (aviso recibido). */
export class ReportarSiniestroViewModel {
  readonly paso = signal<Paso>('formulario');
  readonly polizasStatus = signal<PolizasStatus>('loading');
  readonly polizas = signal<PolizaResumen[]>([]);

  readonly poliza = signal('');
  readonly fechaHecho = signal('');
  readonly descripcion = signal('');
  readonly intentoContinuar = signal(false);

  readonly archivo = signal<File | null>(null);
  readonly errorArchivo = signal<'tipo' | 'tamano' | null>(null);
  readonly ubicacionStatus = signal<UbicacionStatus>('pendiente');
  readonly ubicacion = signal<Ubicacion | null>(null);

  readonly envio = signal<EnvioStatus>('idle');
  readonly rechazo = signal<string | null>(null);
  readonly recibido = signal<AvisoRecibido | null>(null);

  /** Una clave por borrador: reintentar tras un error de red no duplica el aviso. */
  private clave: string;

  readonly hoy: string;
  readonly errores = computed(() => ({
    poliza: !this.poliza(),
    fechaHecho: !this.fechaHecho() || this.fechaHecho() > this.hoy,
    descripcion: !this.descripcion().trim(),
  }));
  readonly formularioValido = computed(() => !Object.values(this.errores()).some(Boolean));
  readonly puedeEnviar = computed(() => !!this.archivo() && this.envio() !== 'enviando');

  constructor(private readonly deps: Dependencias) {
    this.hoy = deps.hoy();
    this.clave = deps.nuevaClave();
  }

  cargarPolizas(): void {
    this.polizasStatus.set('loading');
    this.deps.polizas().subscribe({
      next: (polizas) => {
        const vigentes = polizas.filter((p) => p.estado === 'VIGENTE');
        this.polizas.set(vigentes);
        this.polizasStatus.set(vigentes.length ? 'ready' : 'sin-polizas');
        if (vigentes.length === 1) {
          this.poliza.set(vigentes[0].numero);
        }
      },
      error: () => this.polizasStatus.set('error'),
    });
  }

  ramoSeleccionado(): string | null {
    return this.polizas().find((p) => p.numero === this.poliza())?.producto ?? null;
  }

  continuar(): void {
    this.intentoContinuar.set(true);
    if (this.formularioValido()) {
      this.paso.set('evidencia');
    }
  }

  volverAlFormulario(): void {
    this.paso.set('formulario');
  }

  elegirArchivo(archivo: File | null): void {
    this.errorArchivo.set(null);
    this.rechazo.set(null);
    if (!archivo) {
      this.archivo.set(null);
      return;
    }
    if (!TIPOS_PERMITIDOS.includes(archivo.type)) {
      this.archivo.set(null);
      this.errorArchivo.set('tipo');
      return;
    }
    if (archivo.size > TAMANO_MAXIMO) {
      this.archivo.set(null);
      this.errorArchivo.set('tamano');
      return;
    }
    this.archivo.set(archivo);
  }

  async usarUbicacion(): Promise<void> {
    this.ubicacionStatus.set('solicitando');
    try {
      this.ubicacion.set(await this.deps.ubicar());
      this.ubicacionStatus.set('guardada');
    } catch {
      // Si el usuario bloquea, el aviso sigue sin geoetiqueta (HU-100).
      this.ubicacion.set(null);
      this.ubicacionStatus.set('bloqueada');
    }
  }

  enviar(): void {
    const archivo = this.archivo();
    if (!archivo || this.envio() === 'enviando') {
      return;
    }
    this.envio.set('enviando');
    this.rechazo.set(null);
    this.deps
      .enviar(
        {
          poliza: this.poliza(),
          fechaHecho: this.fechaHecho(),
          descripcion: this.descripcion().trim(),
          archivo,
          ubicacion: this.ubicacion(),
        },
        this.clave,
      )
      .subscribe({
        next: (recibido) => {
          this.recibido.set(recibido);
          this.envio.set('idle');
          this.paso.set('enviado');
        },
        error: (error: unknown) => {
          const rechazo = esRechazoAviso(error);
          if (rechazo) {
            // Un rechazo de negocio no se reintenta igual: el borrador cambia, la clave también.
            this.clave = this.deps.nuevaClave();
            this.rechazo.set(rechazo.mensaje);
            this.envio.set('rechazado');
          } else {
            this.envio.set('error');
          }
        },
      });
  }
}
