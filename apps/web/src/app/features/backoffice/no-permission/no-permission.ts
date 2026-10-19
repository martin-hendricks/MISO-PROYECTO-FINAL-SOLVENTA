import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { Role } from '../../../core/session/session.service';
import { homeSection } from '../sections';

/** `EmptyState / SinPermiso`: replaces the content, never the shell. */
@Component({
  selector: 'sv-no-permission',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, TranslatePipe],
  templateUrl: './no-permission.html',
  styleUrls: ['../backoffice.page.css', './no-permission.css'],
})
export class NoPermission {
  readonly current = input.required<Role | null>();
  readonly required = input.required<Role>();
  protected readonly home = computed(() => ['/cms', homeSection(this.current())]);
}
