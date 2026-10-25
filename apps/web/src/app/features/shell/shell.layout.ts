import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { SessionService } from '../../core/session/session.service';

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

  protected signOut(): void {
    this.session.signOut();
    void this.router.navigateByUrl('/login');
  }
}
