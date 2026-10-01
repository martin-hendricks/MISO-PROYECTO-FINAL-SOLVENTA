import { ChangeDetectionStrategy, Component } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { ShellViewModel } from '../shell/shell.viewmodel';

@Component({
  selector: 'sv-user-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe],
  templateUrl: './user.view.html',
})
export class UserView {
  protected readonly vm = new ShellViewModel();

  constructor() {
    this.vm.activate();
  }
}
