import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DateTimePipe } from '../../core/i18n/format';
import { BilleteraGateway } from '../billetera/billetera.gateway';
import { InicioGateway } from './inicio.gateway';
import { InicioViewModel } from './inicio.viewmodel';

@Component({
  selector: 'sv-inicio',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, TranslatePipe, DateTimePipe],
  templateUrl: './inicio.view.html',
  styleUrls: ['../backoffice/backoffice.page.css', './inicio.view.css'],
})
export class InicioView {
  private readonly gateway = inject(InicioGateway);
  private readonly billetera = inject(BilleteraGateway);
  protected readonly vm = new InicioViewModel(
    () => this.gateway.load(),
    () => new Date(),
    () => this.billetera.list(),
  );

  constructor() {
    this.vm.load();
  }
}
