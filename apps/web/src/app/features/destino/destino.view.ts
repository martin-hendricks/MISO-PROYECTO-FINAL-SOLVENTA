import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { SiniestrosGateway } from '../siniestros/siniestros.gateway';

export type Destino = 'cotizacion' | 'emision' | 'poliza' | 'siniestro' | 'siniestros';

/** Customer destination Inicio links to whose content belongs to a later story. */
@Component({
  selector: 'sv-destino',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, TranslatePipe],
  templateUrl: './destino.view.html',
  styleUrls: ['../backoffice/backoffice.page.css', '../inicio/inicio.view.css'],
})
export class DestinoView implements OnInit {
  private readonly route = inject(ActivatedRoute).snapshot;
  private readonly siniestros = inject(SiniestrosGateway);
  protected readonly destino = this.route.data['destino'] as Destino;
  protected readonly id = this.route.paramMap.get('id');
  protected readonly siniestro = signal('');

  ngOnInit(): void {
    if (this.destino === 'siniestro' || this.destino === 'siniestros') {
      this.siniestros.load().subscribe({
        next: (inicio) => this.siniestro.set(inicio.siniestroEnCurso?.siniestroId ?? ''),
        error: () => this.siniestro.set(''),
      });
    }
  }
}
