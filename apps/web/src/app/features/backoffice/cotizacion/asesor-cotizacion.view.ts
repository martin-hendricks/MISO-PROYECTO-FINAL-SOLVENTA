import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { DateTimePipe, MoneyPipe } from '../../../core/i18n/format';
import { SessionService } from '../../../core/session/session.service';
import { CotizacionGateway } from '../../cotizacion/cotizacion.gateway';
import { RiesgoFields } from '../../cotizacion/riesgo-fields';
import { VidaCrediticiaGateway } from '../../vida-crediticia/vida-crediticia.gateway';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole } from '../sections';
import { AsesorCotizacionViewModel, CampoCliente } from './asesor-cotizacion.viewmodel';

@Component({
  selector: 'sv-asesor-cotizacion',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, NoPermission, RiesgoFields, MoneyPipe, DateTimePipe],
  templateUrl: './asesor-cotizacion.view.html',
  styleUrls: [
    '../backoffice.page.css',
    '../../cotizacion/cotizacion-form.css',
    './asesor-cotizacion.view.css',
  ],
})
export class AsesorCotizacionView {
  private readonly gateway = inject(CotizacionGateway);
  private readonly vidaCrediticia = inject(VidaCrediticiaGateway);
  private readonly translate = inject(TranslateService);
  protected readonly required = requiredRole('cotizaciones');
  protected readonly role = inject(SessionService).role;
  protected readonly allowed = this.role() === this.required;
  protected readonly campos: readonly CampoCliente[] = ['nombre', 'documento'];
  protected readonly vm = new AsesorCotizacionViewModel(
    (ramo) => this.gateway.catalog('asesor', ramo),
    (clienteId, ramo, datos) => this.gateway.quoteFor(clienteId, ramo, datos),
    (clienteId, credito) => this.vidaCrediticia.offerFor(clienteId, credito),
  );

  constructor() {
    const query = inject(ActivatedRoute).snapshot.queryParamMap;
    const cliente = query.get('cliente');
    if (cliente) {
      this.vm.prefill(cliente, query.get('nombre') ?? '', query.get('documento') ?? '');
    }
    if (this.allowed) {
      this.vm.form.loadCatalog();
    }
  }

  /** Profile factors are Solventa attribute codes; show their business name when there is one. */
  protected factor(codigo: string): string {
    const key = `vidaCrediticia.factor.${codigo}`;
    const label = this.translate.instant(key) as string;
    return label === key ? codigo : label;
  }

  protected submit(event: Event): void {
    event.preventDefault();
    this.vm.quote();
  }
}
