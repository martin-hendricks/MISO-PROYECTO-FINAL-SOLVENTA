import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { DateTimePipe } from '../../../core/i18n/format';
import { SessionService } from '../../../core/session/session.service';
import { ConfirmDialog } from '../confirm-dialog/confirm-dialog';
import { NoPermission } from '../no-permission/no-permission';
import { admite, allowedRoles } from '../sections';
import { ALCANCES, SociosGateway } from './socios.gateway';
import { NOMBRE_MAXIMO, SociosViewModel } from './socios.viewmodel';

@Component({
  selector: 'sv-backoffice-socios',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, NoPermission, ConfirmDialog, DateTimePipe],
  templateUrl: './socios.view.html',
  styleUrls: ['../backoffice.page.css', '../backoffice.table.css', './socios.view.css'],
})
export class SociosView {
  private readonly session = inject(SessionService);
  private readonly gateway = inject(SociosGateway);
  protected readonly required = allowedRoles('socios');
  protected readonly role = this.session.role;
  protected readonly subject = this.session.subject;
  protected readonly allowed = admite('socios', this.role());
  protected readonly gestiona = this.role() === 'operador';
  protected readonly alcances = ALCANCES;
  protected readonly nombreMaximo = NOMBRE_MAXIMO;
  protected readonly copiado = signal(false);
  protected readonly vm = new SociosViewModel({
    listar: () => this.gateway.list(),
    crear: (body) => this.gateway.create(body),
    rotar: (socioId) => this.gateway.rotate(socioId),
    revocarCredencial: (socioId, credencialId) =>
      this.gateway.revokeCredential(socioId, credencialId),
    revocar: (socioId) => this.gateway.revoke(socioId),
  });

  constructor() {
    if (this.allowed) {
      this.vm.cargar();
    }
  }

  protected corto(id: string): string {
    return id.slice(0, 8);
  }

  protected copiar(apiKey: string): void {
    const portapapeles = navigator.clipboard as Clipboard | undefined;
    if (!portapapeles) {
      return;
    }
    portapapeles.writeText(apiKey).then(
      () => this.copiado.set(true),
      () => this.copiado.set(false),
    );
  }

  protected cerrarClave(): void {
    this.copiado.set(false);
    this.vm.cerrarClave();
  }
}
