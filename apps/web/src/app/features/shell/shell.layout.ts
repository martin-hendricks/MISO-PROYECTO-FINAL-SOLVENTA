import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { NavigationStart, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { iniciales } from '../../core/session/iniciales';
import { SessionService } from '../../core/session/session.service';
import { PerfilCliente, PerfilGateway } from '../perfil/perfil.gateway';

/** Five customer destinations: Inicio, Pólizas, Siniestros, Billetera,
 * Perfil. "Nueva cotización" stays a filled button, not a sixth destination. */
@Component({
  selector: 'sv-shell-layout',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, TranslatePipe],
  templateUrl: './shell.layout.html',
  styleUrl: './shell.layout.css',
})
export class ShellLayout {
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);
  private readonly perfilGateway = inject(PerfilGateway);

  /** Hamburger overlay state on narrow viewports (<= 600px, see shell.layout.css).
   * Closing the overlay never navigates on its own -- only clicking a
   * destination (or the close button) does, matching "closing the overlay
   * does not change the page" from the HU. */
  protected readonly menuOpen = signal(false);

  /** Avatar initials next to "Cerrar sesión": loaded once per shell instance,
   * not blocking render -- the avatar just stays empty until it resolves
   * (or forever, on a transient error; it is a decorative detail, not
   * something worth retrying or surfacing to the user). */
  private readonly perfil = signal<PerfilCliente | null>(null);
  protected readonly iniciales = computed(() => {
    const perfil = this.perfil();
    return perfil ? iniciales(perfil.nombre, perfil.apellidos, perfil.correo) : '';
  });
  protected readonly nombreCompleto = computed(() => {
    const perfil = this.perfil();
    return perfil ? [perfil.nombre, perfil.apellidos].filter(Boolean).join(' ').trim() : '';
  });

  constructor() {
    // Any navigation (including re-clicking the already-active destination)
    // closes the open overlay, so the menu never stays open over a new page.
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationStart) {
        this.menuOpen.set(false);
      }
    });
    this.perfilGateway.load().subscribe({
      next: (perfil) => this.perfil.set(perfil),
      error: () => undefined,
    });
  }

  protected toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  protected closeMenu(): void {
    this.menuOpen.set(false);
  }

  protected signOut(): void {
    this.session.signOut();
    void this.router.navigateByUrl('/login');
  }
}
