import { ChangeDetectionStrategy, Component } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

/** Step Registro continues to. The consent itself and the sign-up call belong to HU-115. */
@Component({
  selector: 'sv-consentimiento',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe],
  templateUrl: './consentimiento.view.html',
  styleUrl: '../login/login.view.css',
})
export class ConsentimientoView {}
