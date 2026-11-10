import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { SessionService } from '../../../core/session/session.service';
import { NoPermission } from '../no-permission/no-permission';
import { admite, allowedRoles } from '../sections';
import { NotificacionesGateway } from './notificaciones.gateway';
import { NotificacionesViewModel } from './notificaciones.viewmodel';

@Component({
  selector: 'sv-notificaciones',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, NoPermission],
  templateUrl: './notificaciones.view.html',
  styleUrls: ['../backoffice.page.css', '../backoffice.table.css', './notificaciones.view.css'],
})
export class NotificacionesView {
  private readonly gateway = inject(NotificacionesGateway);
  protected readonly required = allowedRoles('notificaciones');
  protected readonly role = inject(SessionService).role;
  protected readonly allowed = admite('notificaciones', this.role());
  protected readonly vm = new NotificacionesViewModel({
    audiencia: () => this.gateway.audiencia(),
    enviar: (body) => this.gateway.enviar(body),
    historial: () => this.gateway.historial(),
  });

  constructor() {
    if (this.allowed) {
      this.vm.cargar();
    }
  }
}
