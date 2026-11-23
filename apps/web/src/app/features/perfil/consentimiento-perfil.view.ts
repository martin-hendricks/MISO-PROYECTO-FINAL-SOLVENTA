import { ChangeDetectionStrategy, Component, inject, input, OnInit } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { capturarFocoActivo, restaurarFoco } from '../../core/a11y/focus-restore';
import { DateTimePipe } from '../../core/i18n/format';
import { ConfirmDialog } from '../backoffice/confirm-dialog/confirm-dialog';
import { ConsentimientoPerfilGateway, TipoConsentimiento } from './consentimiento-perfil.gateway';
import { ConsentimientoPerfilViewModel } from './consentimiento-perfil.viewmodel';
import { PerfilDialog } from './perfil-dialog';

const CLAVES: Record<TipoConsentimiento, string> = {
  datos: 'consentimientoDatos',
  perfil: 'consentimientoPerfil',
};

const TESTID: Record<TipoConsentimiento, string> = {
  datos: 'perfil-datos',
  perfil: 'perfil-consentimiento',
};

@Component({
  selector: 'sv-consentimiento-perfil',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, DateTimePipe, ConfirmDialog, PerfilDialog],
  templateUrl: './consentimiento-perfil.view.html',
  styleUrls: ['./perfil-fila.css', './consentimiento-perfil.view.css'],
})
export class ConsentimientoPerfilView implements OnInit {
  private readonly gateway = inject(ConsentimientoPerfilGateway);

  readonly tipo = input.required<TipoConsentimiento>();

  protected readonly vm = new ConsentimientoPerfilViewModel(
    () => this.gateway.load(this.tipo()),
    () => this.gateway.revoke(this.tipo()),
  );

  private focoPrevio: HTMLElement | null = null;

  ngOnInit(): void {
    this.vm.load();
  }

  protected clave(sufijo: string): string {
    return `${CLAVES[this.tipo()]}.${sufijo}`;
  }

  protected testid(sufijo: string): string {
    return `${TESTID[this.tipo()]}-${sufijo}`;
  }

  protected abrir(): void {
    this.focoPrevio = capturarFocoActivo();
    this.vm.abrir();
  }

  protected cancelar(): void {
    this.vm.cerrar();
    restaurarFoco(this.focoPrevio);
  }
}
