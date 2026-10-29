import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, MoneyPipe } from '../../../core/i18n/format';
import { SessionService } from '../../../core/session/session.service';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole } from '../sections';
import { CotizacionesGateway } from './cotizaciones.gateway';
import { CotizacionesViewModel } from './cotizaciones.viewmodel';

/** The advisor's quotes pending issuance (HU-163). */
@Component({
  selector: 'sv-backoffice-cotizaciones',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, NoPermission, RouterLink, MoneyPipe, DatePipe],
  templateUrl: './cotizaciones.view.html',
  styleUrls: ['../backoffice.page.css', './cotizaciones.view.css'],
})
export class CotizacionesView {
  private readonly session = inject(SessionService);
  private readonly gateway = inject(CotizacionesGateway);
  protected readonly required = requiredRole('cotizaciones');
  protected readonly role = this.session.role;
  protected readonly subject = this.session.subject;
  protected readonly allowed = this.role() === this.required;
  protected readonly vm = new CotizacionesViewModel((filtro) => this.gateway.list(filtro));

  constructor() {
    if (this.allowed) {
      this.vm.load();
    }
  }
}
