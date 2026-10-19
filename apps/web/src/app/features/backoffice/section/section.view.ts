import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { SessionService } from '../../../core/session/session.service';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole, Section } from '../sections';

/** Destination whose content belongs to a later story: title plus permission check. */
@Component({
  selector: 'sv-backoffice-section',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, NoPermission],
  templateUrl: './section.view.html',
  styleUrl: '../backoffice.page.css',
})
export class SectionView {
  private readonly session = inject(SessionService);
  protected readonly section = inject(ActivatedRoute).snapshot.data['section'] as Section;
  protected readonly required = requiredRole(this.section);
  protected readonly role = this.session.role;
  protected readonly subject = this.session.subject;
  protected readonly allowed = computed(() => this.role() === this.required);
}
