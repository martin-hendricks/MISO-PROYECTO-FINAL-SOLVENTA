import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, MoneyPipe } from '../../../core/i18n/format';
import { claveEstado } from '../estado-siniestro';
import { SiniestrosGateway } from '../siniestros.gateway';
import { SiniestrosListaViewModel } from './siniestros-lista.viewmodel';

/** HU-117 / HU-160: Mis siniestros con el estado del núcleo. Solo consulta. */
@Component({
  selector: 'sv-siniestros-lista',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe, DatePipe],
  templateUrl: './siniestros-lista.view.html',
  styleUrls: [
    '../../polizas/polizas.page.css',
    '../../polizas/lista/polizas-lista.view.css',
    '../siniestros.css',
  ],
})
export class SiniestrosListaView {
  private readonly gateway = inject(SiniestrosGateway);
  protected readonly vm = new SiniestrosListaViewModel(() => this.gateway.list());
  protected readonly claveEstado = claveEstado;

  constructor() {
    this.vm.load();
  }
}
