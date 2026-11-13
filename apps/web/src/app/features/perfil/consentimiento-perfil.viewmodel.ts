import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { ConsentimientoPerfil } from './consentimiento-perfil.gateway';

export class ConsentimientoPerfilViewModel {
  private readonly estadoState = signal<ConsentimientoPerfil | null>(null);
  private readonly dialogoState = signal(false);
  private readonly revocandoState = signal(false);
  private readonly errorState = signal(false);

  readonly dialogo = this.dialogoState.asReadonly();
  readonly revocando = this.revocandoState.asReadonly();
  readonly error = this.errorState.asReadonly();

  readonly visible = computed(() => {
    const estado = this.estadoState()?.estado;
    return estado === 'vigente' || estado === 'revocado';
  });
  readonly otorgadoEn = computed(() => {
    const estado = this.estadoState();
    return estado?.estado === 'vigente' ? estado.otorgadoEn : null;
  });
  readonly revocadoEn = computed(() => {
    const estado = this.estadoState();
    return estado?.estado === 'revocado' ? estado.revocadoEn : null;
  });

  constructor(
    private readonly cargar: () => Observable<ConsentimientoPerfil>,
    private readonly revocarEnNucleo: () => Observable<ConsentimientoPerfil>,
  ) {}

  load(): void {
    this.cargar().subscribe({
      next: (estado) => this.estadoState.set(estado),
      error: () => this.estadoState.set(null),
    });
  }

  abrir(): void {
    this.errorState.set(false);
    this.dialogoState.set(true);
  }

  cerrar(): void {
    this.dialogoState.set(false);
  }

  revocar(): void {
    if (this.revocandoState()) {
      return;
    }
    this.revocandoState.set(true);
    this.revocarEnNucleo().subscribe({
      next: (estado) => {
        this.estadoState.set(estado);
        this.revocandoState.set(false);
        this.dialogoState.set(false);
      },
      error: () => {
        this.errorState.set(true);
        this.revocandoState.set(false);
        this.dialogoState.set(false);
      },
    });
  }
}
