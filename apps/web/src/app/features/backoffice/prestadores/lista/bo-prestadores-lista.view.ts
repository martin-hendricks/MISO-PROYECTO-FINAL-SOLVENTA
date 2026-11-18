import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { GoogleMapsLoaderService } from '../../../../core/maps/google-maps-loader.service';
import { SessionService } from '../../../../core/session/session.service';
import { MapaPrestadoresComponent } from '../../../prestadores/mapa-prestadores/mapa-prestadores.component';
import { CENTRO_BOGOTA, RAMOS_PRESTADOR } from '../../../prestadores/tipo-prestador';
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
  protected readonly centroBogota = CENTRO_BOGOTA;
  protected readonly mapa = signal(this.loader.estado());
  protected readonly vm = new BoPrestadoresListaViewModel(
    {
      listar: (filtro) => this.gateway.listar(filtro),
      cambiarEstado: (id, estado) => this.gateway.cambiarEstado(id, estado),
    },
    this.role() === 'operador',
  );

  constructor() {
    void this.loader.cargar().then((estado) => this.mapa.set(estado));
    if (this.allowed) {
      this.vm.cargar();
    }
  }

  protected centroMapa(): { lat: number; lng: number } {
    const primero = this.vm.prestadores()[0];
    if (!primero) {
      return this.centroBogota;
    }
    return this.vm.centro() ?? { lat: primero.lat, lng: primero.lng };
  }
}
