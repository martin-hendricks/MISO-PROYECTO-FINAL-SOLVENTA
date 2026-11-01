import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, MoneyPipe } from '../../../core/i18n/format';
import { PolizasGateway } from '../polizas.gateway';
import { PolizaDetalleViewModel } from './poliza-detalle.viewmodel';

@Component({
  selector: 'sv-poliza-detalle',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe, DatePipe],
  templateUrl: './poliza-detalle.view.html',
  styleUrls: ['../polizas.page.css', './poliza-detalle.view.css'],
})
export class PolizaDetalleView {
  private readonly gateway = inject(PolizasGateway);
  // The `polizas/:numero` route always carries the param.
  private readonly numero = inject(ActivatedRoute).snapshot.paramMap.get('numero')!;
  protected readonly vm = new PolizaDetalleViewModel(() => this.gateway.detail(this.numero));

  constructor() {
    this.vm.load();
  }
}
