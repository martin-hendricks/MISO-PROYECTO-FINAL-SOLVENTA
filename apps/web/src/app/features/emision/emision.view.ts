import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, MoneyPipe } from '../../core/i18n/format';
import { EmisionGateway } from './emision.gateway';
import { EmisionViewModel } from './emision.viewmodel';

/** Customer issuance outside the shell: no destinations while the core issues. */
@Component({
  selector: 'sv-emision',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe, DatePipe],
  templateUrl: './emision.view.html',
  styleUrls: ['../polizas/polizas.page.css', './emision.view.css'],
})
export class EmisionView {
  private readonly gateway = inject(EmisionGateway);
  private readonly router = inject(Router);
  private readonly query = inject(ActivatedRoute).snapshot.queryParamMap;
  private readonly cotizacionId = this.query.get('cotizacion');
  protected readonly valid = !!this.cotizacionId;
  protected readonly vm = new EmisionViewModel(
    () => this.gateway.accept({ cotizacionId: this.cotizacionId! }),
    (motivo) => void this.router.navigate(['/suscripcion-rechazada'], { state: { motivo } }),
  );

  constructor() {
    if (this.valid) {
      this.vm.issue();
    }
  }
}
