import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { RegistroDraft } from './registro.draft';
import { RegistroField, RegistroViewModel } from './registro.viewmodel';

interface Field {
  name: RegistroField;
  type: 'text' | 'email' | 'password';
  autocomplete: string;
}

const FIELDS: readonly Field[] = [
  { name: 'nombre', type: 'text', autocomplete: 'given-name' },
  { name: 'apellidos', type: 'text', autocomplete: 'family-name' },
  { name: 'documento', type: 'text', autocomplete: 'off' },
  { name: 'correo', type: 'email', autocomplete: 'email' },
  { name: 'contrasena', type: 'password', autocomplete: 'new-password' },
];

@Component({
  selector: 'sv-registro',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, TranslatePipe],
  templateUrl: './registro.view.html',
  styleUrl: '../login/login.view.css',
})
export class RegistroView {
  private readonly router = inject(Router);
  private readonly draft = inject(RegistroDraft);
  protected readonly fields = FIELDS;
  protected readonly vm = new RegistroViewModel((alta) => {
    this.draft.save(alta);
    void this.router.navigateByUrl('/consentimiento');
  });

  protected submit(event: Event): void {
    event.preventDefault();
    this.vm.submit();
  }
}
