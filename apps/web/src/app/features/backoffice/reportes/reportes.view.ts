import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { SessionService } from '../../../core/session/session.service';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole } from '../sections';
import { ReporteGenerado, ReportesGateway } from './reportes.gateway';
import { ReporteTipo, ReportesViewModel } from './reportes.viewmodel';

function hoyIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function haceDiasIso(dias: number): string {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() - dias);
  return fecha.toISOString().slice(0, 10);
}

@Component({
  selector: 'sv-reportes',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, NoPermission],
  templateUrl: './reportes.view.html',
  styleUrls: ['../backoffice.page.css', './reportes.view.css'],
})
export class ReportesView {
  private readonly gateway = inject(ReportesGateway);
  protected readonly required = requiredRole('reportes');
  protected readonly role = inject(SessionService).role;
  protected readonly allowed = this.role() === this.required;

  // HU-62/HU-63 no especifican un selector de rango en el Gherkin -- 30 días
  // hacia atrás es el mismo rango por defecto que ya usa bff-web/ms-polizas
  // (RANGO_POR_DEFECTO_DIAS en routers/reportes.py) cuando no se pasan
  // desde/hasta, así que esta UI no necesita inputs de fecha para el camino
  // feliz: "generar" pide exactamente lo mismo que pediría un cliente HTTP
  // sin parámetros.
  protected readonly desde = signal(haceDiasIso(30));
  protected readonly hasta = signal(hoyIso());

  protected readonly vm = new ReportesViewModel(
    (desde, hasta) => this.gateway.regulador(desde, hasta),
    (desde, hasta) => this.gateway.reaseguradora(desde, hasta),
  );

  protected generar(tipo: ReporteTipo): void {
    this.vm.generar(tipo, this.desde(), this.hasta());
  }

  protected descargar(reporte: ReporteGenerado): void {
    const blob = new Blob([reporte.contenido], { type: reporte.tipoContenido });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = reporte.nombreArchivo;
    enlace.click();
    URL.revokeObjectURL(url);
  }
}
