import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe } from '../../../core/i18n/format';
import { PolizasGateway } from '../polizas.gateway';
import { PolizasAvisosViewModel } from './polizas-avisos.viewmodel';

@Component({
  selector: 'sv-polizas-avisos',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, DatePipe],
  templateUrl: './polizas-avisos.view.html',
  styleUrls: ['../polizas.page.css', './polizas-avisos.view.css'],
})
export class PolizasAvisosView {
  private readonly gateway = inject(PolizasGateway);
  protected readonly vm = new PolizasAvisosViewModel(() => this.gateway.avisos());

  constructor() {
    this.vm.load();
  }
}
