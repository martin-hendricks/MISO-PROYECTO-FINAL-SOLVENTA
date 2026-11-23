import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, DateTimePipe, MoneyPipe } from '../../../core/i18n/format';
import { SessionService } from '../../../core/session/session.service';
import { ConfirmDialog } from '../confirm-dialog/confirm-dialog';
import { NoPermission } from '../no-permission/no-permission';
import { admite, allowedRoles } from '../sections';
import { AvisosGateway, FILTROS } from './avisos.gateway';
import { AvisosViewModel } from './avisos.viewmodel';

/** Destino Avisos del back-office: cola a la izquierda, caso a la derecha, sin navegar. */
@Component({
  selector: 'sv-avisos',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, MoneyPipe, DatePipe, DateTimePipe, NoPermission, ConfirmDialog],
  templateUrl: './avisos.view.html',
  styleUrls: ['../backoffice.page.css', '../backoffice.table.css', './avisos.view.css'],
})
export class AvisosView {
  private readonly gateway = inject(AvisosGateway);
  protected readonly required = allowedRoles('avisos');
  protected readonly role = inject(SessionService).role;
  protected readonly allowed = admite('avisos', this.role());
  protected readonly filtros = FILTROS;

  protected readonly vm = new AvisosViewModel({
    cola: (filtro) => this.gateway.cola(filtro),
    caso: (id) => this.gateway.caso(id),
    decidir: (id, decision, motivo) => this.gateway.decidir(id, decision, motivo),
    enrutar: (id, motivo) => this.gateway.enrutarAPerito(id, motivo),
    pagar: (id) => this.gateway.pagar(id),
  });

  constructor() {
    if (this.allowed) {
      this.vm.cargar();
    }
  }

  protected onSeleccionar(event: KeyboardEvent, id: string): void {
    event.preventDefault(); // Space would otherwise scroll the page
    this.vm.seleccionar(id);
  }
}
