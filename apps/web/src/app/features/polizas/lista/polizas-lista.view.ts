import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, MoneyPipe } from '../../../core/i18n/format';
import { PolizasGateway } from '../polizas.gateway';
import { PolizasListaViewModel } from './polizas-lista.viewmodel';

@Component({
  selector: 'sv-polizas-lista',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe, DatePipe],
  templateUrl: './polizas-lista.view.html',
  styleUrls: ['../polizas.page.css', './polizas-lista.view.css'],
})
export class PolizasListaView {
  private readonly gateway = inject(PolizasGateway);
  protected readonly vm = new PolizasListaViewModel(() => this.gateway.list());

  constructor() {
    this.vm.load();
  }
}
