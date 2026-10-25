import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

export type Destino = 'cotizacion' | 'emision' | 'poliza' | 'siniestro' | 'vidaCrediticia';

/** Customer destination Inicio links to whose content belongs to a later story. */
@Component({
  selector: 'sv-destino',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, TranslatePipe],
  templateUrl: './destino.view.html',
  styleUrls: ['../backoffice/backoffice.page.css', '../inicio/inicio.view.css'],
})
export class DestinoView {
  private readonly route = inject(ActivatedRoute).snapshot;
  protected readonly destino = this.route.data['destino'] as Destino;
  protected readonly id = this.route.paramMap.get('id');
}
