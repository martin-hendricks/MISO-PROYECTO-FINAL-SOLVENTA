import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

/** Modal with a scrim over the content it opens on top of (not a new route),
 * optionally requiring a non-blank reason before the confirm CTA enables --
 * same pattern SOLV-120 (HU-27, aprobar/rechazar aviso) will reuse. */
@Component({
  selector: 'sv-confirm-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe],
  templateUrl: './confirm-dialog.html',
  styleUrl: './confirm-dialog.css',
})
export class ConfirmDialog {
  readonly titulo = input.required<string>();
  readonly advertencia = input.required<string>();
  readonly requiereMotivo = input(false);
  readonly confirmarTexto = input('backoffice.confirmDialog.confirmar');

  protected readonly motivo = signal('');
  protected readonly puedeConfirmar = computed(
    () => !this.requiereMotivo() || this.motivo().trim().length > 0,
  );

  readonly cancelar = output<void>();
  readonly confirmar = output<string>();

  protected onConfirmar(): void {
    if (!this.puedeConfirmar()) {
      return;
    }
    this.confirmar.emit(this.motivo().trim());
  }
}
