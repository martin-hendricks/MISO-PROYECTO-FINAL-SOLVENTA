import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { GoogleMapsLoaderService } from '../../../core/maps/google-maps-loader.service';
import { GEOLOCATION_PORT } from '../geolocation-port';
import { MapaPrestadoresComponent } from '../mapa-prestadores/mapa-prestadores.component';
import { PrestadoresGateway } from '../prestadores.gateway';
import { CIUDADES_PRESTADOR, RAMOS_PRESTADOR } from '../tipo-prestador';
import { PrestadoresMapaViewModel } from './prestadores-mapa.viewmodel';

@Component({
  selector: 'sv-prestadores-mapa',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MapaPrestadoresComponent],
  templateUrl: './prestadores-mapa.view.html',
  styleUrls: ['../../polizas/polizas.page.css', './prestadores-mapa.view.css'],
})
export class PrestadoresMapaView {
  private readonly gateway = inject(PrestadoresGateway);
  private readonly loader = inject(GoogleMapsLoaderService);
  private readonly claimId = inject(ActivatedRoute).snapshot.paramMap.get('id');

  protected readonly vm = new PrestadoresMapaViewModel(
    {
      cercanos: (consulta) => this.gateway.buscar(consulta),
      porSiniestro: (id) => this.gateway.porSiniestro(id),
    },
    inject(GEOLOCATION_PORT),
    this.claimId,
  );
  protected readonly mapa = signal(this.loader.estado());
  protected readonly ramos = RAMOS_PRESTADOR;
  protected readonly ciudades = CIUDADES_PRESTADOR;

  constructor() {
    void this.loader.cargar().then((estado) => {
      this.mapa.set(estado);
      this.vm.fijarMapa(estado);
    });
    this.vm.cargar();
  }

  protected mapaNoDisponible(): void {
    this.mapa.set('no-disponible');
    this.vm.fijarMapa('no-disponible');
  }
}
