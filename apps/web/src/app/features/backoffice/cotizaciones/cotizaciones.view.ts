import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { SessionService } from '../../../core/session/session.service';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole } from '../sections';

/** Entry to the advisor quotes: the list belongs to a later story, the new quote is HU-10. */
@Component({
  selector: 'sv-backoffice-cotizaciones',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, TranslatePipe, NoPermission],
  templateUrl: './cotizaciones.view.html',
  styleUrl: '../backoffice.page.css',
})
export class CotizacionesView {
  private readonly session = inject(SessionService);
  protected readonly required = requiredRole('cotizaciones');
  protected readonly role = this.session.role;
  protected readonly subject = this.session.subject;
  protected readonly allowed = this.role() === this.required;
}
