import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { SessionService } from '../../core/session/session.service';
import { LoginViewModel } from './login.viewmodel';

@Component({
  selector: 'sv-login',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe],
  templateUrl: './login.view.html',
  styleUrl: './login.view.css',
})
export class LoginView {
  private readonly router = inject(Router);
  protected readonly vm = new LoginViewModel(inject(SessionService), () => {
    void this.router.navigateByUrl('/user');
  });

  protected submit(event: Event): void {
    event.preventDefault();
    this.vm.submit();
  }
}
