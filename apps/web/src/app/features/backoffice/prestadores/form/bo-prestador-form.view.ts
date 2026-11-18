import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { GoogleMapsLoaderService } from '../../../../core/maps/google-maps-loader.service';
import { MapaPrestadoresComponent } from '../../../prestadores/mapa-prestadores/mapa-prestadores.component';
import {
  CENTRO_BOGOTA,
  CIUDADES_PRESTADOR,
  RAMOS_PRESTADOR,
  TIPOS_PRESTADOR,
} from '../../../prestadores/tipo-prestador';
import { BoPrestadoresGateway } from '../bo-prestadores.gateway';
import { BoPrestadorFormViewModel } from './bo-prestador-form.viewmodel';

@Component({
  selector: 'sv-bo-prestador-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, MapaPrestadoresComponent],
  templateUrl: './bo-prestador-form.view.html',
  styleUrls: ['../../backoffice.page.css', './bo-prestador-form.view.css'],
})
export class BoPrestadorFormView {
  private readonly gateway = inject(BoPrestadoresGateway);
  private readonly loader = inject(GoogleMapsLoaderService);
  private readonly router = inject(Router);
  private readonly id = inject(ActivatedRoute).snapshot.paramMap.get('id');

  protected readonly vm = new BoPrestadorFormViewModel(
    {
      obtener: (prestadorId) => this.gateway.obtener(prestadorId),
      guardar: (entrada, prestadorId) =>
        prestadorId ? this.gateway.editar(prestadorId, entrada) : this.gateway.crear(entrada),
    },
    this.id,
  );
  protected readonly mapa = signal(this.loader.estado());
  protected readonly tipos = TIPOS_PRESTADOR;
  protected readonly ramos = RAMOS_PRESTADOR;
  protected readonly ciudades = CIUDADES_PRESTADOR;
  protected readonly centro = CENTRO_BOGOTA;

  constructor() {
    void this.loader.cargar().then((estado) => {
      this.mapa.set(estado);
      if (estado === 'disponible' && this.vm.lat() === null) {
        this.vm.fijarPin(this.centro.lat, this.centro.lng);
      }
    });
    this.vm.cargar();
    effect(() => {
      if (this.vm.guardado()) {
        void this.router.navigateByUrl('/cms/prestadores');
      }
    });
  }

  protected pin(): { lat: number; lng: number } {
    return {
      lat: this.vm.lat() ?? this.centro.lat,
      lng: this.vm.lng() ?? this.centro.lng,
    };
  }
}
