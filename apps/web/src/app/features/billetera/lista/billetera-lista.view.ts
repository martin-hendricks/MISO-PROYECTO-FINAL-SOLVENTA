import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, MoneyPipe } from '../../../core/i18n/format';
import { LocaleService } from '../../../core/i18n/locale.service';
import { BilleteraGateway } from '../billetera.gateway';
import { BilleteraListaViewModel, FiltroBilletera } from './billetera-lista.viewmodel';

@Component({
  selector: 'sv-billetera-lista',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe, DatePipe],
  templateUrl: './billetera-lista.view.html',
  styleUrls: [
    '../../polizas/polizas.page.css',
    '../../polizas/lista/polizas-lista.view.css',
    '../../siniestros/siniestros.css',
    './billetera-lista.view.css',
  ],
})
export class BilleteraListaView {
  private readonly gateway = inject(BilleteraGateway);
  private readonly locale = inject(LocaleService);
  protected readonly filtros: FiltroBilletera[] = ['todos', 'asistido', 'otras', 'pago_automatico'];
  protected readonly vm = new BilleteraListaViewModel(
    () => this.gateway.list(),
    () => this.locale.monedaInicio(),
  );

  constructor() {
    this.vm.load();
  }
}
