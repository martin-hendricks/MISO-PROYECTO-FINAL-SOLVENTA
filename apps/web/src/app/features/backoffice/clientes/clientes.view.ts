import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { SessionService } from '../../../core/session/session.service';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole } from '../sections';
import { ClientesGateway } from './clientes.gateway';
import { ClientesViewModel } from './clientes.viewmodel';

const KPIS = ['active', 'web', 'android', 'pendingConsent'] as const;

@Component({
  selector: 'sv-backoffice-clientes',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, NoPermission],
  templateUrl: './clientes.view.html',
  styleUrls: ['../backoffice.page.css', './clientes.view.css'],
})
export class ClientesView {
  private readonly session = inject(SessionService);
  private readonly gateway = inject(ClientesGateway);
  protected readonly kpis = KPIS;
  protected readonly required = requiredRole('clientes');
  protected readonly role = this.session.role;
  protected readonly subject = this.session.subject;
  protected readonly allowed = this.role() === this.required;
  protected readonly vm = new ClientesViewModel(() => this.gateway.list());

  constructor() {
    if (this.allowed) {
      this.vm.load();
    }
  }
}
