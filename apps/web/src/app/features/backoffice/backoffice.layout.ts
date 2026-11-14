import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { SessionService } from '../../core/session/session.service';
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
  protected readonly role = this.session.role;
  /** Notificaciones only appears for a role that can open it. The other
   * destinations stay in the nav and fail closed inside the section. */
  protected readonly sections = computed(() =>
    SECTIONS.filter((section) => section !== 'notificaciones' || admite(section, this.role())),
  );

  protected signOut(): void {
    this.session.signOut();
    void this.router.navigateByUrl('/cms/login');
  }
}
