import { signal } from '@angular/core';
import { Observable } from 'rxjs';
import { ReporteGenerado } from './reportes.gateway';

export type ReporteTipo = 'regulador' | 'reaseguradora';
export type ReporteStatus = 'idle' | 'generando' | 'listo' | 'error';

export class ReportesViewModel {
  private readonly statusState = signal<Record<ReporteTipo, ReporteStatus>>({
    regulador: 'idle',
    reaseguradora: 'idle',
  });
  readonly status = this.statusState.asReadonly();

  private readonly reporteState = signal<Record<ReporteTipo, ReporteGenerado | null>>({
    regulador: null,
    reaseguradora: null,
  });
  readonly reporte = this.reporteState.asReadonly();

  constructor(
    private readonly reguladorSource: (desde: string, hasta: string) => Observable<ReporteGenerado>,
    private readonly reaseguradoraSource: (desde: string, hasta: string) => Observable<ReporteGenerado>,
  ) {}

  generar(tipo: ReporteTipo, desde: string, hasta: string): void {
    this.statusState.update((actual) => ({ ...actual, [tipo]: 'generando' }));
    const source = tipo === 'regulador' ? this.reguladorSource : this.reaseguradoraSource;
    source(desde, hasta).subscribe({
      next: (reporte) => {
        this.reporteState.update((actual) => ({ ...actual, [tipo]: reporte }));
        this.statusState.update((actual) => ({ ...actual, [tipo]: 'listo' }));
      },
      error: () => this.statusState.update((actual) => ({ ...actual, [tipo]: 'error' })),
    });
  }
}
