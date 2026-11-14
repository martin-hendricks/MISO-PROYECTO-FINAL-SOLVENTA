import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { SessionService } from '../../../core/session/session.service';
import { ConfirmDialog } from '../confirm-dialog/confirm-dialog';
import { NoPermission } from '../no-permission/no-permission';
import { admite, allowedRoles } from '../sections';
import { Cliente, ClientesGateway } from './clientes.gateway';
import { nombreCliente, pushDe, ClientesViewModel } from './clientes.viewmodel';

@Component({
  selector: 'sv-backoffice-clientes',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, NoPermission, RouterLink, ConfirmDialog],
  templateUrl: './clientes.view.html',
  styleUrls: ['../backoffice.page.css', '../backoffice.table.css', './clientes.view.css'],
})
export class ClientesView {
  private readonly session = inject(SessionService);
  private readonly gateway = inject(ClientesGateway);
  protected readonly required = allowedRoles('clientes');
  protected readonly role = this.session.role;
  protected readonly subject = this.session.subject;
  protected readonly allowed = admite('clientes', this.role());
  protected readonly nombre = nombreCliente;
  protected readonly push = pushDe;
  protected readonly vm = new ClientesViewModel(
    {
      listar: (consulta) => this.gateway.list(consulta),
      crear: (body) => this.gateway.create(body),
      editar: (usuarioId, body) => this.gateway.update(usuarioId, body),
      cambiarEstado: (usuarioId, estado) => this.gateway.setEstado(usuarioId, estado),
    },
    this.role() === 'operador',
  );

  constructor() {
    if (this.allowed) {
      this.vm.cargar();
    }
  }

  protected cotizarDe(cliente: Cliente): { cliente: string; nombre: string; documento: string } {
    return {
      cliente: cliente.usuarioId,
      nombre: nombreCliente(cliente),
      documento: cliente.documento,
    };
  }
}
