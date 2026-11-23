import { A11yModule } from '@angular/cdk/a11y';
import { ChangeDetectionStrategy, Component, HostListener, input, output } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  selector: 'sv-perfil-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, A11yModule],
  templateUrl: './perfil-dialog.html',
  styleUrls: ['../backoffice/confirm-dialog/confirm-dialog.css', './perfil-dialog.css'],
})
export class PerfilDialog {
  readonly titulo = input.required<string>();
  readonly texto = input<string>('');
  readonly cerrar = output<void>();

  @HostListener('keydown.escape')
  protected onEscape(): void {
    this.cerrar.emit();
  }
}
