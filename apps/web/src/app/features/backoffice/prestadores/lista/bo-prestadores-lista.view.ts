import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { LocaleService } from '../../../../core/i18n/locale.service';
import { GoogleMapsLoaderService } from '../../../../core/maps/google-maps-loader.service';
import { SessionService } from '../../../../core/session/session.service';
import { MapaPrestadoresComponent } from '../../../prestadores/mapa-prestadores/mapa-prestadores.component';
import {
  PAIS_POR_LOCALE,
  PAISES,
  RAMOS_PRESTADOR,
} from '../../../prestadores/tipo-prestador';
import { ConfirmDialog } from '../../confirm-dialog/confirm-dialog';
import { NoPermission } from '../../no-permission/no-permission';
import { admite, allowedRoles } from '../../sections';
import { BoPrestadoresGateway } from '../bo-prestadores.gateway';
import { BoPrestadoresListaViewModel } from './bo-prestadores-lista.viewmodel';

@Component({
  selector: 'sv-bo-prestadores-lista',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink, ConfirmDialog, NoPermission, MapaPrestadoresComponent],
  templateUrl: './bo-prestadores-lista.view.html',
  styleUrls: [
    '../../backoffice.page.css',
    '../../backoffice.table.css',
    './bo-prestadores-lista.view.css',
  ],
})
export class BoPrestadoresListaView {
  private readonly session = inject(SessionService);
  private readonly gateway = inject(BoPrestadoresGateway);
  private readonly loader = inject(GoogleMapsLoaderService);

  protected readonly required = allowedRoles('prestadores');
  protected readonly role = this.session.role;
  protected readonly allowed = admite('prestadores', this.role());
  protected readonly ramos = RAMOS_PRESTADOR;
  protected readonly paises = PAISES;
  protected readonly mapa = signal(this.loader.estado());
  protected readonly vm = new BoPrestadoresListaViewModel(
    {
      listar: (filtro) => this.gateway.listar(filtro),
      ciudades: (pais) => this.gateway.ciudades(pais),
      cambiarEstado: (id, estado) => this.gateway.cambiarEstado(id, estado),
    },
    this.role() === 'operador',
    PAIS_POR_LOCALE[inject(LocaleService).locale()],
  );

  constructor() {
    void this.loader.cargar().then((estado) => this.mapa.set(estado));
    if (this.allowed) {
      this.vm.iniciar();
    }
  }
}
