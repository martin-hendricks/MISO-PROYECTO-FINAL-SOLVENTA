import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { LocaleService } from '../../../../core/i18n/locale.service';
import { GoogleMapsLoaderService } from '../../../../core/maps/google-maps-loader.service';
import { MapaPrestadoresComponent } from '../../../prestadores/mapa-prestadores/mapa-prestadores.component';
import {
  PAIS_POR_LOCALE,
  PAISES,
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
      ciudades: (pais) => this.gateway.ciudades(pais),
      guardar: (entrada, prestadorId) =>
        prestadorId ? this.gateway.editar(prestadorId, entrada) : this.gateway.crear(entrada),
    },
    this.id,
    PAIS_POR_LOCALE[inject(LocaleService).locale()],
  );
  protected readonly mapa = signal(this.loader.estado());
  protected readonly tipos = TIPOS_PRESTADOR;
  protected readonly ramos = RAMOS_PRESTADOR;
  protected readonly paises = PAISES;

  constructor() {
    void this.loader.cargar().then((estado) => this.mapa.set(estado));
    this.vm.cargar();
    effect(() => {
      if (this.mapa() === 'disponible' && this.vm.pin()) {
        this.vm.anclarPin();
      }
    });
    effect(() => {
      if (this.vm.guardado()) {
        void this.router.navigateByUrl('/cms/prestadores');
      }
    });
  }
}
