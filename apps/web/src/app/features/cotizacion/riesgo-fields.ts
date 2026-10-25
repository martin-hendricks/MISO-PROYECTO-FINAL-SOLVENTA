import { ChangeDetectionStrategy, Component, inject, input } from '@angular/core';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { MoneyPipe } from '../../core/i18n/format';
import { CotizacionFormViewModel } from './cotizacion-form.viewmodel';

/** Line picker and the risk data of the chosen line, shared by customer and advisor. */
@Component({
  selector: 'sv-riesgo-fields',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, MoneyPipe],
  templateUrl: './riesgo-fields.html',
  styleUrl: './cotizacion-form.css',
  host: { style: 'display: contents' },
})
export class RiesgoFields {
  private readonly translate = inject(TranslateService);
  readonly vm = input.required<CotizacionFormViewModel>();
  /** Id prefix so two forms never share label targets. */
  readonly prefix = input('cotizacion');

  /** Catalog values are codes (`bogota`); show the translated name when there is one. */
  protected etiqueta(valor: string): string {
    const key = `cotizacion.valor.${valor}`;
    const label = this.translate.instant(key) as string;
    return label === key ? valor : label;
  }
}
