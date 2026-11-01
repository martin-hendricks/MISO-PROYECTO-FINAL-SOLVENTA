import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { DateTimePipe, MoneyPipe } from '../../core/i18n/format';
import { CotizacionGateway } from '../cotizacion/cotizacion.gateway';
import { VidaCrediticiaGateway } from './vida-crediticia.gateway';
import { CAMPOS_CREDITO, VidaCrediticiaViewModel } from './vida-crediticia.viewmodel';

/** The core names the mortgage life product this way in its catalog (bff-web RAMO_A_PRODUCTO). */
const RAMO = 'Vida crediticia';

/** Card Vida Crediticia of Inicio (HU-105): consentimiento-hipotecario, then oferta-hipotecario. */
@Component({
  selector: 'sv-vida-crediticia',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe, DateTimePipe],
  templateUrl: './vida-crediticia.view.html',
  styleUrls: [
    '../polizas/polizas.page.css',
    '../cotizacion/cotizacion-form.css',
    './vida-crediticia.view.css',
  ],
})
export class VidaCrediticiaView {
  private readonly translate = inject(TranslateService);
  private readonly cotizacion = inject(CotizacionGateway);
  private readonly gateway = inject(VidaCrediticiaGateway);
  protected readonly campos = CAMPOS_CREDITO;
  protected readonly vm = new VidaCrediticiaViewModel(
    () => this.cotizacion.catalog('cliente', RAMO),
    (credito) => this.gateway.offer(credito),
  );

  constructor() {
    this.vm.loadCatalog();
  }

  /** Factors are Solventa attribute codes; show their business name when there is one. */
  protected factor(codigo: string): string {
    const key = `vidaCrediticia.factor.${codigo}`;
    const label = this.translate.instant(key) as string;
    return label === key ? codigo : label;
  }

  protected submit(event: Event): void {
    event.preventDefault();
    this.vm.authorize();
  }
}
