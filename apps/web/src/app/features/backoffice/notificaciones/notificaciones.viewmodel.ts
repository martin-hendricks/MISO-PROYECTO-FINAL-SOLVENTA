import { computed, signal } from '@angular/core';
import { forkJoin, Observable } from 'rxjs';
import {
  AudienciaDifusion,
  DifusionEntrada,
  DifusionItem,
  DifusionResultado,
  UsuarioAudiencia,
} from './notificaciones.gateway';

export const LIMITE_TITULO = 80;
export const LIMITE_CUERPO = 240;

export interface PuertosNotificaciones {
  audiencia: () => Observable<{ usuarios: UsuarioAudiencia[] }>;
  enviar: (body: DifusionEntrada) => Observable<DifusionResultado>;
  historial: () => Observable<{ items: DifusionItem[] }>;
}

export class NotificacionesViewModel {
  readonly titulo = signal('');
  readonly cuerpo = signal('');
  readonly modo = signal<'todos' | 'usuarios'>('todos');
  readonly elegidos = signal<readonly string[]>([]);
  readonly poliza = signal('');
  readonly audiencia = signal<UsuarioAudiencia[]>([]);
  readonly historial = signal<DifusionItem[]>([]);
  readonly resultado = signal<DifusionResultado | null>(null);
  readonly enviando = signal(false);
  readonly status = signal<'loading' | 'ready' | 'error'>('loading');
  readonly errorEnvio = signal(false);

  readonly restantesTitulo = computed(() => LIMITE_TITULO - this.titulo().trim().length);
  readonly restantesCuerpo = computed(() => LIMITE_CUERPO - this.cuerpo().trim().length);
  readonly vistaPrevia = computed(() => ({ titulo: this.titulo(), cuerpo: this.cuerpo() }));
  readonly puedeEnviar = computed(() => {
    const titulo = this.titulo().trim();
    const cuerpo = this.cuerpo().trim();
    if (!titulo || titulo.length > LIMITE_TITULO) {
      return false;
    }
    if (!cuerpo || cuerpo.length > LIMITE_CUERPO) {
      return false;
    }
    if (this.modo() === 'usuarios' && this.elegidos().length === 0) {
      return false;
    }
    return !this.enviando();
  });

  constructor(private readonly puertos: PuertosNotificaciones) {}

  cargar(): void {
    this.status.set('loading');
    forkJoin({
      audiencia: this.puertos.audiencia(),
      historial: this.puertos.historial(),
    }).subscribe({
      next: ({ audiencia, historial }) => {
        this.audiencia.set(audiencia.usuarios);
        this.historial.set(historial.items);
        this.status.set('ready');
      },
      error: () => this.status.set('error'),
    });
  }

  elegirModo(modo: 'todos' | 'usuarios'): void {
    this.modo.set(modo);
  }

  persona(usuario: UsuarioAudiencia): string {
    const legal = [usuario?.nombre, usuario?.apellidos]
      .map((parte) => (parte ?? '').trim())
      .filter((parte) => parte.length > 0)
      .join(' ');
    return legal || (usuario?.email ?? '').trim();
  }

  documento(usuario: UsuarioAudiencia): string {
    return (usuario?.documento ?? '').trim();
  }

  etiqueta(usuario: UsuarioAudiencia): string {
    return [this.persona(usuario), this.documento(usuario)]
      .filter((parte) => parte.length > 0)
      .join(' · ');
  }

  alternar(usuarioId: string): void {
    this.elegidos.update((actual) =>
      actual.includes(usuarioId) ? actual.filter((id) => id !== usuarioId) : [...actual, usuarioId],
    );
  }

  enviar(): void {
    if (!this.puedeEnviar()) {
      return;
    }
    const audiencia: AudienciaDifusion =
      this.modo() === 'todos'
        ? { tipo: 'todos' }
        : { tipo: 'usuarios', usuarioIds: [...this.elegidos()] };
    const poliza = this.poliza().trim();
    const body: DifusionEntrada = {
      titulo: this.titulo().trim(),
      cuerpo: this.cuerpo().trim(),
      audiencia,
      ...(poliza ? { poliza } : {}),
    };
    this.enviando.set(true);
    this.errorEnvio.set(false);
    this.puertos.enviar(body).subscribe({
      next: (resultado) => {
        this.resultado.set(resultado);
        this.enviando.set(false);
        this.puertos.historial().subscribe({
          next: (historial) => this.historial.set(historial.items),
          error: () => this.status.set('error'),
        });
      },
      error: () => {
        this.enviando.set(false);
        this.errorEnvio.set(true);
      },
    });
  }
}
