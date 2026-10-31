import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { NavigationStart, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { SessionService } from '../../core/session/session.service';

/** Four customer destinations (HU-107/SOLV-231): Inicio, Pólizas, Siniestros,
 * Perfil. "Nueva cotización" is a filled CTA, not a fifth underlined
 * destination -- it keeps its own styling in the template/CSS. */
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

  /** Hamburger overlay state on narrow viewports (<= 600px, see shell.layout.css).
   * Closing the overlay never navigates on its own -- only clicking a
   * destination (or the close button) does, matching "closing the overlay
   * does not change the page" from the HU. */
  protected readonly menuOpen = signal(false);

  constructor() {
    // Any navigation (including re-clicking the already-active destination)
    // closes the open overlay, so the menu never stays open over a new page.
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationStart) {
        this.menuOpen.set(false);
      }
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
