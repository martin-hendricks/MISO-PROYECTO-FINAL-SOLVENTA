import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, DateTimePipe, MoneyPipe } from '../../../core/i18n/format';
import { SessionService } from '../../../core/session/session.service';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole } from '../sections';
import { AsesorEmisionGateway } from './asesor-emision.gateway';
import { AsesorEmisionViewModel } from './asesor-emision.viewmodel';

@Component({
  selector: 'sv-asesor-emision',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, NoPermission, MoneyPipe, DatePipe, DateTimePipe],
  templateUrl: './asesor-emision.view.html',
  styleUrls: ['../backoffice.page.css', './asesor-emision.view.css'],
})
export class AsesorEmisionView {
  private readonly gateway = inject(AsesorEmisionGateway);
  private readonly route = inject(ActivatedRoute).snapshot;
  // The `cotizaciones/:cotizacionId/emision` route always carries the param.
  protected readonly cotizacionId = this.route.paramMap.get('cotizacionId')!;
  private readonly ofertaId = this.route.queryParamMap.get('oferta');
  protected readonly clienteId = this.route.queryParamMap.get('cliente');
  protected readonly valid = !!this.ofertaId && !!this.clienteId;
  protected readonly required = requiredRole('cotizaciones');
  protected readonly role = inject(SessionService).role;
  protected readonly allowed = this.role() === this.required;
  protected readonly vm = new AsesorEmisionViewModel(
    () =>
      this.gateway.decide({
        cotizacionId: this.cotizacionId,
        ofertaId: this.ofertaId!,
        clienteId: this.clienteId!,
      }),
    (solicitudId) => this.gateway.issue(solicitudId),
  );

  constructor() {
    if (this.allowed && this.valid) {
      this.vm.load();
    }
  }
}
