import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { IdiomaRegionView } from '../idioma-region/idioma-region.view';

export type Destino =
  | 'cotizacion'
  | 'emision'
  | 'poliza'
  | 'siniestro'
  | 'siniestros'
  | 'perfil'
  | 'vidaCrediticia';

/** Customer destination Inicio links to whose content belongs to a later
 * story. Perfil (HU-108) is the one exception: it already hosts the
 * idioma-region dialog, ahead of the full Hub Perfil (TASK-91, a separate
 * unassigned story) -- changing locale mid-session is a self-contained
 * action that does not depend on the rest of that hub existing yet. */
@Component({
  selector: 'sv-destino',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, TranslatePipe, IdiomaRegionView],
  templateUrl: './destino.view.html',
  styleUrls: ['../backoffice/backoffice.page.css', '../inicio/inicio.view.css'],
})
export class DestinoView {
  private readonly route = inject(ActivatedRoute).snapshot;
  protected readonly destino = this.route.data['destino'] as Destino;
  protected readonly id = this.route.paramMap.get('id');
  protected readonly idiomaRegionOpen = signal(false);
}
