import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe } from '../../../core/i18n/format';
import { SessionService } from '../../../core/session/session.service';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole } from '../sections';
import { MetricasGateway } from './metricas.gateway';
import { MetricasViewModel } from './metricas.viewmodel';

function hoyIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function haceDiasIso(dias: number): string {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() - dias);
  return fecha.toISOString().slice(0, 10);
}

const RANGO_DIAS = 30;

@Component({
  selector: 'sv-metricas',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, DatePipe, NoPermission],
  templateUrl: './metricas.view.html',
  styleUrls: ['../backoffice.page.css', './metricas.view.css'],
})
export class MetricasView {
  private readonly gateway = inject(MetricasGateway);
  protected readonly required = requiredRole('metricas');
  protected readonly role = inject(SessionService).role;
  protected readonly allowed = this.role() === this.required;

  protected readonly vm = new MetricasViewModel((desde, hasta) =>
    this.gateway.conteos(desde, hasta),
  );

  constructor() {
    if (this.allowed) {
      this.vm.load(haceDiasIso(RANGO_DIAS), hoyIso());
    }
  }

  protected reintentar(): void {
    this.vm.load(haceDiasIso(RANGO_DIAS), hoyIso());
  }
}
