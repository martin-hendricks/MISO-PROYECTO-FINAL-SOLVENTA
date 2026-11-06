import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { DateTimePipe, MoneyPipe } from '../../core/i18n/format';
import { CotizacionGateway } from '../cotizacion/cotizacion.gateway';
import { Credito, VIDA_ETAPA_MS, VidaCrediticiaGateway } from './vida-crediticia.gateway';
import { CAMPOS_CREDITO, ETAPAS, VidaCrediticiaViewModel } from './vida-crediticia.viewmodel';

/** The core names the mortgage life product this way in its catalog (bff-web RAMO_A_PRODUCTO). */
const RAMO = 'Vida hipotecario';

/** Card Vida Crediticia of Inicio (HU-105): consentimiento-hipotecario, then oferta-hipotecario. */
@Component({
  selector: 'sv-vida-crediticia',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MoneyPipe, DateTimePipe],
  templateUrl: './vida-crediticia.view.html',
  styleUrls: [
    '../polizas/polizas.page.css',
    '../cotizacion/cotizacion-form.css',
    '../cotizacion/oferta/ver-oferta.view.css',
    './vida-crediticia.view.css',
  ],
})
export class VidaCrediticiaView {
  private readonly translate = inject(TranslateService);
  private readonly cotizacion = inject(CotizacionGateway);
  private readonly gateway = inject(VidaCrediticiaGateway);
  private readonly route = inject(ActivatedRoute);
  protected readonly campos = CAMPOS_CREDITO;
  protected readonly etapas = ETAPAS;
  protected readonly vm = new VidaCrediticiaViewModel(
    () => this.cotizacion.catalog('cliente', RAMO),
    (credito) => this.gateway.offer(credito),
    inject(VIDA_ETAPA_MS),
  );

  constructor() {
    this.vm.loadCatalog();
    const enviado = this.creditoDeLaUrl();
    if (enviado) {
      this.vm.prefill(enviado);
      return;
    }
    this.gateway.originacion().subscribe((credito) => {
      if (credito) {
        this.vm.prefill(credito);
      }
    });
  }

  /** Nueva cotización sends the mortgage along, so the page fills even if saving it failed. */
  private creditoDeLaUrl(): Credito | null {
    const params = this.route.snapshot.queryParamMap;
    const valor = Number(params.get('valor'));
    const plazoMeses = Number(params.get('plazoMeses'));
    return valor > 0 && plazoMeses > 0 ? { valor, plazoMeses } : null;
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
