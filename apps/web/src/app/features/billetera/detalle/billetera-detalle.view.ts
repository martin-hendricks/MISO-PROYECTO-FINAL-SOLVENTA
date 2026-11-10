import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { MoneyPipe } from '../../../core/i18n/format';
import { BilleteraGateway } from '../billetera.gateway';
import { BilleteraDetalleViewModel } from './billetera-detalle.viewmodel';

@Component({
  selector: 'sv-billetera-detalle',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe],
  templateUrl: './billetera-detalle.view.html',
  styleUrls: [
    '../../polizas/polizas.page.css',
    '../../siniestros/siniestros.css',
    '../../siniestros/detalle/siniestro-detalle.view.css',
    './billetera-detalle.view.css',
  ],
})
export class BilleteraDetalleView {
  private readonly gateway = inject(BilleteraGateway);
  private readonly route = inject(ActivatedRoute);
  protected readonly vm = new BilleteraDetalleViewModel(() =>
    this.gateway.detail(this.route.snapshot.paramMap.get('id') ?? ''),
  );

  constructor() {
    this.vm.load();
  }
}
