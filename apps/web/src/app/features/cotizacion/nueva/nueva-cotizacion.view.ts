import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { CotizacionFormViewModel } from '../cotizacion-form.viewmodel';
import { CotizacionGateway } from '../cotizacion.gateway';
import { Credito, VidaCrediticiaGateway } from '../../vida-crediticia/vida-crediticia.gateway';
import { RiesgoFields } from '../riesgo-fields';

/** The line whose quote is the profiled mortgage life offer of /vida-crediticia. */
const RAMO_HIPOTECARIO = 'hipotecario';

/** Customer quote of the single line of business (HU-104); success opens the offer. */
@Component({
  selector: 'sv-nueva-cotizacion',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, RiesgoFields],
  templateUrl: './nueva-cotizacion.view.html',
  styleUrls: ['../cotizacion-form.css', './nueva-cotizacion.view.css'],
})
export class NuevaCotizacionView {
  private readonly gateway = inject(CotizacionGateway);
  private readonly vida = inject(VidaCrediticiaGateway);
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
    if (this.vm.ramo().id === RAMO_HIPOTECARIO && this.vm.canQuote()) {
      this.continuarHipotecario();
      return;
    }
    this.vm.quote();
  }

  /** Mortgage life is priced with the customer's profile: it continues in /vida-crediticia. */
  private continuarHipotecario(): void {
    const credito: Credito = { valor: this.vm.numero('valor'), plazoMeses: this.vm.numero('plazoMeses') };
    const abrir = () =>
      void this.router.navigate(['/vida-crediticia'], { queryParams: { ...credito } });
    this.vida.registrarOriginacion(credito).subscribe({ next: abrir, error: abrir });
  }
}
