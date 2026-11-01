import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, MoneyPipe } from '../../../core/i18n/format';
import { SessionService } from '../../../core/session/session.service';
import { ConfirmDialog } from '../confirm-dialog/confirm-dialog';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole } from '../sections';
import { PolizasBackofficeGateway } from './polizas-backoffice.gateway';
import { PolizaBackofficeDetalleViewModel } from './poliza-backoffice-detalle.viewmodel';

@Component({
  selector: 'sv-poliza-backoffice-detalle',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, MoneyPipe, DatePipe, NoPermission, ConfirmDialog],
  templateUrl: './poliza-backoffice-detalle.view.html',
  styleUrls: ['../backoffice.page.css', './poliza-backoffice-detalle.view.css'],
})
export class PolizaBackofficeDetalleView {
  private readonly gateway = inject(PolizasBackofficeGateway);
  private readonly router = inject(Router);
  protected readonly numero = inject(ActivatedRoute).snapshot.paramMap.get('numero');
  protected readonly required = requiredRole('polizas');
  protected readonly role = inject(SessionService).role;
  protected readonly allowed = this.role() === this.required;

  protected readonly busqueda = signal('');
  protected readonly dialogoCancelarAbierto = signal(false);

  protected readonly vm = new PolizaBackofficeDetalleViewModel(
    () => this.gateway.buscarPorNumero(this.numero!),
    () => this.gateway.renovar(this.numero!),
    (motivo) => this.gateway.cancelar(this.numero!, motivo),
  );

  constructor() {
    if (this.allowed && this.numero) {
      this.vm.load();
    }
  }

  protected buscar(): void {
    const numero = this.busqueda().trim();
    if (numero) {
      void this.router.navigate(['/cms/polizas', numero]);
    }
  }

  protected abrirCancelar(): void {
    this.dialogoCancelarAbierto.set(true);
  }

  protected confirmarCancelar(motivo: string): void {
    this.dialogoCancelarAbierto.set(false);
    this.vm.cancelar(motivo);
  }
}
