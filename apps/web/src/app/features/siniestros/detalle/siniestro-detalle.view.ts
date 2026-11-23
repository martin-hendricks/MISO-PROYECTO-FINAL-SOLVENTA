import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, DateTimePipe, MoneyPipe } from '../../../core/i18n/format';
import { claveEstado } from '../estado-siniestro';
import { SiniestrosGateway } from '../siniestros.gateway';
import { SiniestroDetalleViewModel } from './siniestro-detalle.viewmodel';

/** HU-111: el cliente sigue su caso con el estado del núcleo. No aprueba, rechaza ni paga. */
@Component({
  selector: 'sv-siniestro-detalle',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe, DatePipe, DateTimePipe],
  templateUrl: './siniestro-detalle.view.html',
  styleUrls: [
    '../../polizas/polizas.page.css',
    '../siniestros.css',
    './siniestro-detalle.view.css',
  ],
})
export class SiniestroDetalleView {
  private readonly gateway = inject(SiniestrosGateway);
  private readonly id = inject(ActivatedRoute).snapshot.paramMap.get('id')!;
  protected readonly vm = new SiniestroDetalleViewModel(() => this.gateway.detail(this.id));
  protected readonly claveEstado = claveEstado;

  constructor() {
    this.vm.load();
  }
}
