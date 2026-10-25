import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { CotizacionFormViewModel } from './cotizacion-form.viewmodel';
import { CAMPOS_RANGO } from './soat-motocicleta';

/** SOAT motocicleta risk data, shared by the customer and advisor quotes. */
@Component({
  selector: 'sv-riesgo-fields',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe],
  templateUrl: './riesgo-fields.html',
  styleUrl: './cotizacion-form.css',
  host: { style: 'display: contents' },
})
export class RiesgoFields {
  readonly vm = input.required<CotizacionFormViewModel>();
  /** Id prefix so two forms never share label targets. */
  readonly prefix = input('cotizacion');
  protected readonly campos = CAMPOS_RANGO;
}
