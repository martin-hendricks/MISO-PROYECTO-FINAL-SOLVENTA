import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { CotizacionFormViewModel } from '../cotizacion-form.viewmodel';
import { CotizacionGateway } from '../cotizacion.gateway';
import { RiesgoFields } from '../riesgo-fields';

/** Customer quote of the single line of business (HU-104); success opens the offer. */
@Component({
  selector: 'sv-nueva-cotizacion',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, RiesgoFields],
  templateUrl: './nueva-cotizacion.view.html',
  styleUrls: ['../../polizas/polizas.page.css', '../cotizacion-form.css'],
})
export class NuevaCotizacionView {
  private readonly gateway = inject(CotizacionGateway);
  private readonly router = inject(Router);
  protected readonly vm = new CotizacionFormViewModel(
    (ramo) => this.gateway.catalog('cliente', ramo),
    (ramo, datos) => this.gateway.quote(ramo, datos),
    (oferta) => void this.router.navigate(['/cotizaciones', oferta.cotizacionId]),
  );

  constructor() {
    this.vm.loadCatalog();
  }

  protected submit(event: Event): void {
    event.preventDefault();
    this.vm.quote();
  }
}
