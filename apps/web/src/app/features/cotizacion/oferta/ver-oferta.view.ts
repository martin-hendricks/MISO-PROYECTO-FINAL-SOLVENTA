import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DateTimePipe, MoneyPipe } from '../../../core/i18n/format';
import { CotizacionGateway } from '../cotizacion.gateway';
import { VerOfertaViewModel } from './ver-oferta.viewmodel';

/** Firm offer by id (HU-113): reconsulting never recalculates; "Aceptar" starts HU-114. */
@Component({
  selector: 'sv-ver-oferta',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe, DateTimePipe],
  templateUrl: './ver-oferta.view.html',
  styleUrls: ['../../polizas/polizas.page.css', '../cotizacion-form.css', './ver-oferta.view.css'],
})
export class VerOfertaView {
  private readonly gateway = inject(CotizacionGateway);
  // The `cotizaciones/:cotizacionId` route always carries the param.
  private readonly cotizacionId = inject(ActivatedRoute).snapshot.paramMap.get('cotizacionId')!;
  protected readonly vm = new VerOfertaViewModel(() => this.gateway.find(this.cotizacionId));

  constructor() {
    this.vm.load();
  }
}
