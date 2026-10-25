import { computed, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { EmisionAsesor, SolicitudEmision } from './asesor-emision.gateway';

export type AsesorEmisionStatus =
  'loading' | 'approved' | 'rejected' | 'issuing' | 'issued' | 'error';

export class AsesorEmisionViewModel {
  private readonly statusState = signal<AsesorEmisionStatus>('loading');
  readonly status = this.statusState.asReadonly();

  private readonly solicitudState = signal<SolicitudEmision | null>(null);
  readonly solicitud = this.solicitudState.asReadonly();

  private readonly emisionState = signal<EmisionAsesor | null>(null);
  readonly poliza = computed(() => this.emisionState()?.poliza ?? null);

  /** Steps as the core reports them: the issuance answer supersedes the decision. */
  readonly pasos = computed(() => this.emisionState()?.pasos ?? this.solicitudState()?.pasos ?? []);

  /** Only a request the core approved can be issued. */
  private approvedId: string | null = null;
  private failedOn: 'decision' | 'issuance' = 'decision';

  constructor(
    private readonly decide: () => Observable<SolicitudEmision>,
    private readonly issueSource: (solicitudId: string) => Observable<EmisionAsesor>,
  ) {}

  load(): void {
    this.statusState.set('loading');
    this.failedOn = 'decision';
    this.decide().subscribe({
      next: (solicitud) => {
        const approved = solicitud.decision.resultado === 'ACEPTADA';
        this.solicitudState.set(solicitud);
        this.approvedId = approved ? solicitud.solicitudId : null;
        this.statusState.set(approved ? 'approved' : 'rejected');
      },
      error: () => this.statusState.set('error'),
    });
  }

  issue(): void {
    if (!this.approvedId) {
      return;
    }
    this.statusState.set('issuing');
    this.failedOn = 'issuance';
    this.issueSource(this.approvedId).subscribe({
      next: (emision) => {
        this.emisionState.set(emision);
        this.statusState.set('issued');
      },
      error: () => this.statusState.set('error'),
    });
  }

  retry(): void {
    if (this.failedOn === 'issuance') {
      this.issue();
    } else {
      this.load();
    }
  }
}
