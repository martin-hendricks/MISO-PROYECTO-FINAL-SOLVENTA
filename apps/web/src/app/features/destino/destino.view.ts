import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { IdiomaRegionView } from '../idioma-region/idioma-region.view';
import { PerfilGateway } from '../perfil/perfil.gateway';
import { SiniestrosGateway } from '../siniestros/siniestros.gateway';

export type Destino = 'cotizacion' | 'emision' | 'poliza' | 'siniestro' | 'siniestros' | 'perfil';

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
export class DestinoView implements OnInit {
  private readonly route = inject(ActivatedRoute).snapshot;
  private readonly perfil = inject(PerfilGateway);
  private readonly siniestros = inject(SiniestrosGateway);
  protected readonly destino = this.route.data['destino'] as Destino;
  protected readonly id = this.route.paramMap.get('id');
  protected readonly idiomaRegionOpen = signal(false);
  protected readonly nombre = signal('');
  protected readonly siniestro = signal('');

  ngOnInit(): void {
    if (this.destino === 'perfil') {
      this.perfil.load().subscribe({
        next: (cuenta) => this.nombre.set(`${cuenta.nombre} ${cuenta.apellidos}`.trim()),
        error: () => this.nombre.set(''),
      });
    }
    if (this.destino === 'siniestro' || this.destino === 'siniestros') {
      this.siniestros.load().subscribe({
        next: (inicio) => this.siniestro.set(inicio.siniestroEnCurso?.siniestroId ?? ''),
        error: () => this.siniestro.set(''),
      });
    }
  }
}
