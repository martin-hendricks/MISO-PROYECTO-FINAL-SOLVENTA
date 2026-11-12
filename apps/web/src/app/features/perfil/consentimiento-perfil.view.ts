import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { DateTimePipe } from '../../core/i18n/format';
import { ConfirmDialog } from '../backoffice/confirm-dialog/confirm-dialog';
import { ConsentimientoPerfilGateway } from './consentimiento-perfil.gateway';
import { ConsentimientoPerfilViewModel } from './consentimiento-perfil.viewmodel';

@Component({
  selector: 'sv-consentimiento-perfil',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, DateTimePipe, ConfirmDialog],
  templateUrl: './consentimiento-perfil.view.html',
  styleUrl: './consentimiento-perfil.view.css',
})
export class ConsentimientoPerfilView {
  private readonly gateway = inject(ConsentimientoPerfilGateway);
  protected readonly vm = new ConsentimientoPerfilViewModel(
    () => this.gateway.load(),
    () => this.gateway.revoke(),
  );

  constructor() {
    this.vm.load();
  }
}
