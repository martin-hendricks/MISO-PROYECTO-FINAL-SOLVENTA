import { LowerCasePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { SessionService } from '../../../core/session/session.service';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole } from '../sections';
import { formatDate, formatMoney } from './cotizacion.format';
import { CotizacionGateway } from './cotizacion.gateway';
import { CotizacionViewModel, TIPOS, VALOR_ASEGURADO, VIGENCIAS } from './cotizacion.viewmodel';

const RAMOS = ['dispositivo', 'viaje', 'vida', 'clima', 'pagos', 'hipotecario'] as const;

@Component({
  selector: 'sv-backoffice-cotizacion',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [LowerCasePipe, RouterLink, TranslatePipe, NoPermission],
  templateUrl: './cotizacion.view.html',
  styleUrls: ['../backoffice.page.css', './cotizacion.view.css'],
})
export class CotizacionView {
  private readonly session = inject(SessionService);
  /** `provideSolventaI18n` always starts with a language set. */
  private readonly locale = inject(TranslateService).getCurrentLang() as string;
  protected readonly ramos = RAMOS;
  protected readonly ramo = RAMOS[0];
  protected readonly vigencias = VIGENCIAS;
  protected readonly tipos = TIPOS;
  protected readonly required = requiredRole('cotizaciones');
  protected readonly role = this.session.role;
  protected readonly allowed = this.role() === this.required;
  protected readonly vm = new CotizacionViewModel(inject(CotizacionGateway));

  protected readonly rango = {
    min: formatMoney(VALOR_ASEGURADO.min, VALOR_ASEGURADO.moneda, this.locale),
    max: formatMoney(VALOR_ASEGURADO.max, VALOR_ASEGURADO.moneda, this.locale),
    moneda: VALOR_ASEGURADO.moneda,
  };

  protected readonly oferta = computed(() => {
    const offer = this.vm.offer();
    if (!offer) {
      return null;
    }
    const money = (amount: number) => formatMoney(amount, offer.moneda, this.locale);
    return {
      cotizacionId: offer.cotizacionId,
      prima: `${money(offer.prima)} ${offer.moneda}`,
      primaNeta: money(offer.primaNeta),
      gastosExpedicion: money(offer.gastosExpedicion),
      vigenciaMeses: offer.vigenciaMeses,
      venceEn: formatDate(offer.venceEn, this.locale),
    };
  });

  protected calculate(event: Event): void {
    event.preventDefault();
    this.vm.calculate();
  }
}
