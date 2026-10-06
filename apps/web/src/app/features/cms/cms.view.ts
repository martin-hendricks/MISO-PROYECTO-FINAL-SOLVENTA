import { ChangeDetectionStrategy, Component } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { ShellViewModel } from '../shell/shell.viewmodel';

@Component({
  selector: 'sv-cms-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe],
  templateUrl: './cms.view.html',
})
export class CmsView {
  protected readonly vm = new ShellViewModel();

  constructor() {
    this.vm.activate();
  }
}
