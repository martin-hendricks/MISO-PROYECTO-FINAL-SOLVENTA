import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { LocaleService } from '../../../core/i18n/locale.service';
import { GoogleMapsLoaderService } from '../../../core/maps/google-maps-loader.service';
import { GEOLOCATION_PORT } from '../geolocation-port';
import { MapaPrestadoresComponent } from '../mapa-prestadores/mapa-prestadores.component';
import { PrestadoresGateway } from '../prestadores.gateway';
import { TarjetaPrestadorComponent } from '../tarjeta/tarjeta-prestador.component';
import { RAMOS_PRESTADOR } from '../tipo-prestador';
import { PrestadoresMapaViewModel } from './prestadores-mapa.viewmodel';

@Component({
  selector: 'sv-prestadores-mapa',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MapaPrestadoresComponent, TarjetaPrestadorComponent],
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
      ciudades: (pais) => this.gateway.ciudades(pais),
      porSiniestro: (id, area) => this.gateway.porSiniestro(id, area),
    },
    inject(GEOLOCATION_PORT),
    this.claimId,
    inject(LocaleService).locale,
  );
  protected readonly ramos = RAMOS_PRESTADOR;
  protected readonly idsSeleccion = computed(() =>
    this.vm.seleccion().map((prestador) => prestador.id),
  );

  constructor() {
    this.vm.fijarMapa(this.loader.estado());
    void this.loader.cargar().then((estado) => this.vm.fijarMapa(estado));
    this.vm.cargar();
  }

  protected slug(nombre: string): string {
    return nombre
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }
}
