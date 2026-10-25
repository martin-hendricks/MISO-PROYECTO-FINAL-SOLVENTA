import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { InicioGateway } from './inicio.gateway';
import { InicioViewModel } from './inicio.viewmodel';

@Component({
  selector: 'sv-inicio',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, TranslatePipe],
  templateUrl: './inicio.view.html',
  styleUrls: ['../backoffice/backoffice.page.css', './inicio.view.css'],
})
export class InicioView {
  private readonly gateway = inject(InicioGateway);
  protected readonly vm = new InicioViewModel(() => this.gateway.load());

  constructor() {
    this.vm.load();
  }
}
