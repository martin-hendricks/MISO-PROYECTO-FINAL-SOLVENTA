import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { iniciales } from '../../core/session/iniciales';
import { SessionService } from '../../core/session/session.service';
import { PerfilBackoffice, PerfilBackofficeGateway } from './perfil-backoffice.gateway';
import { admite, SECTIONS } from './sections';

@Component({
  selector: 'sv-backoffice-layout',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, TranslatePipe],
  templateUrl: './backoffice.layout.html',
  styleUrl: './backoffice.layout.css',
})
export class BackofficeLayout {
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);
  private readonly perfilGateway = inject(PerfilBackofficeGateway);
  protected readonly role = this.session.role;
  /** Notificaciones only appears for a role that can open it. The other
   * destinations stay in the nav and fail closed inside the section. */
  protected readonly sections = computed(() =>
    SECTIONS.filter((section) => section !== 'notificaciones' || admite(section, this.role())),
  );

  /** Avatar initials next to "Cerrar sesión", same pattern as ShellLayout
   * (customer portal) -- loaded once per layout instance, no retry. */
  private readonly perfil = signal<PerfilBackoffice | null>(null);
  protected readonly iniciales = computed(() => {
    const perfil = this.perfil();
    return perfil ? iniciales(perfil.nombre, perfil.apellidos, perfil.correo) : '';
  });
  protected readonly nombreCompleto = computed(() => {
    const perfil = this.perfil();
    return perfil ? [perfil.nombre, perfil.apellidos].filter(Boolean).join(' ').trim() : '';
  });

  constructor() {
    this.perfilGateway.load().subscribe({
      next: (perfil) => this.perfil.set(perfil),
      error: () => undefined,
    });
  }

  protected signOut(): void {
    this.session.signOut();
    void this.router.navigateByUrl('/cms/login');
  }
}
