import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { Motivo } from '../emision.gateway';

@Component({
  selector: 'sv-suscripcion-rechazada',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink],
  templateUrl: './suscripcion-rechazada.view.html',
  styleUrls: ['../../polizas/polizas.page.css', './suscripcion-rechazada.view.css'],
})
export class SuscripcionRechazadaView {
  /** Reason handed over by the issuance view; `history.state` keeps it across a reload. */
  protected readonly motivo: Motivo | null =
    (history.state as { motivo?: Motivo } | null)?.motivo ?? null;
}
