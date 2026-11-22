import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { capturarFocoActivo, restaurarFoco } from '../../core/a11y/focus-restore';
import { LocaleService } from '../../core/i18n/locale.service';
import { SessionService } from '../../core/session/session.service';
import { ConfirmDialog } from '../backoffice/confirm-dialog/confirm-dialog';
import { IdiomaRegionView } from '../idioma-region/idioma-region.view';
import { ConsentimientoPerfilView } from './consentimiento-perfil.view';
import { PerfilDialog } from './perfil-dialog';
import { PerfilCliente, PerfilGateway } from './perfil.gateway';

type Dialogo = 'idioma' | 'cerrarSesion' | null;

@Component({
  selector: 'sv-perfil',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, ConfirmDialog, IdiomaRegionView, ConsentimientoPerfilView, PerfilDialog],
  templateUrl: './perfil.view.html',
  styleUrls: [
    '../polizas/polizas.page.css',
    '../backoffice/backoffice.page.css',
    './perfil-fila.css',
    './perfil.view.css',
  ],
})
export class PerfilView {
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);
  private readonly localeService = inject(LocaleService);

  protected readonly locale = this.localeService.locale;
  protected readonly moneda = computed(() => {
    this.locale();
    return this.localeService.monedaInicio();
  });
  protected readonly identidad = signal('');
  protected readonly dialogo = signal<Dialogo>(null);

  private focoPrevio: HTMLElement | null = null;

  constructor() {
    inject(PerfilGateway)
      .load()
      .subscribe({
        next: (perfil) => this.identidad.set(identidadDe(perfil)),
        error: () => this.identidad.set(''),
      });
  }

  protected abrir(dialogo: Exclude<Dialogo, null>): void {
    this.focoPrevio = capturarFocoActivo();
    this.dialogo.set(dialogo);
  }

  protected cerrar(): void {
    this.dialogo.set(null);
    restaurarFoco(this.focoPrevio);
  }

  protected cerrarSesion(): void {
    this.session.signOut();
    void this.router.navigateByUrl('/login');
  }
}

function identidadDe(perfil: PerfilCliente): string {
  const nombre = `${perfil.nombre} ${perfil.apellidos}`.trim();
  const numero = /^\d+$/.test(perfil.documento)
    ? perfil.documento.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
    : perfil.documento;
  const documento = [perfil.tipoDocumento, numero].filter(Boolean).join(' ');
  return [nombre, documento].filter(Boolean).join(' · ');
}
