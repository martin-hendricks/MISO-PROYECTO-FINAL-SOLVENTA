import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { MoneyPipe } from '../../../core/i18n/format';
import { PolizasGateway } from '../../polizas/polizas.gateway';
import { SiniestrosGateway } from '../siniestros.gateway';
import { ParametricoViewModel } from './parametrico.viewmodel';

@Component({
  selector: 'sv-parametrico',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe],
  templateUrl: './parametrico.view.html',
  styleUrl: './parametrico.view.css',
})
export class ParametricoView {
  private readonly claims = inject(SiniestrosGateway);
  private readonly policies = inject(PolizasGateway);
  protected readonly vm = new ParametricoViewModel(
    () => this.claims.parametric(),
    (numero, enabled) => this.policies.preference(numero, enabled),
  );

  constructor() {
    this.vm.open();
  }

  protected renovar(event: Event): void {
    this.vm.chooseRenewal((event.target as HTMLInputElement).checked);
  }
}
