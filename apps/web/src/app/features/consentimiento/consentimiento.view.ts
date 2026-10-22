import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { map } from 'rxjs';
import { SessionService } from '../../core/session/session.service';
import { CUSTOMER_LOGIN } from '../login/login.variant';
import { RegistroDraft } from '../registro/registro.draft';
import { ConsentimientoGateway } from './consentimiento.gateway';
import { ConsentimientoViewModel } from './consentimiento.viewmodel';

/** consentimiento-datos: the last step of the sign-up. `requireDraft` guarantees its data. */
@Component({
  selector: 'sv-consentimiento',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe],
  templateUrl: './consentimiento.view.html',
  styleUrls: ['../login/login.view.css', './consentimiento.view.css'],
})
export class ConsentimientoView {
  private readonly router = inject(Router);
  private readonly draft = inject(RegistroDraft);
  private readonly session = inject(SessionService);
  private readonly gateway = inject(ConsentimientoGateway);

  protected readonly vm = new ConsentimientoViewModel(
    () =>
      this.gateway.grant(this.draft.alta()!).pipe(
        map((registro) => {
          if (!registro.consentimiento?.habeasData) {
            throw new Error('Consentimiento sin registrar');
          }
          this.session.start(registro);
        }),
      ),
    () => {
      this.draft.clear();
      void this.router.navigateByUrl(CUSTOMER_LOGIN.home);
    },
  );

  protected submit(event: Event): void {
    event.preventDefault();
    this.vm.submit();
  }

  /** Without consent there is no account: the sign-up data is dropped. */
  protected decline(): void {
    this.draft.clear();
    void this.router.navigateByUrl('/login');
  }
}
