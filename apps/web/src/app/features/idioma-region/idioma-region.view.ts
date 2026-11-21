import { ChangeDetectionStrategy, Component, computed, inject, input, output } from '@angular/core';
import { Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { formatDate, formatMoney } from '../../core/i18n/format';
import { Locale, LocaleService, LOCALES } from '../../core/i18n/locale.service';

/** Preview shown under the options (HU-108 "Locale México formatea en el
 * canal"): the same sample premium and date, formatted with the selected
 * locale so the visitor sees what changes before confirming. Only the
 * presentation changes -- the amount is identical for every locale. */
const SAMPLE_PREMIUM = 1234.56;
const SAMPLE_DATE = '2026-07-09';
const CURRENCY: Record<Locale, string> = {
  'es-CO': 'COP',
  'es-MX': 'MXN',
  'es-CL': 'CLP',
  'es-PE': 'PEN',
};

/** HU-108: Español · Colombia/México/Chile/Perú. Two hosts share this
 * component instead of duplicating the picker:
 * - the /idioma-region ROUTE (first launch, requireLocaleChosen guard, no
 *   session yet): `embedded` is false (default), Continuar navigates to
 *   /registro.
 * - a DIALOG opened from Perfil (sv-destino, already signed in): `embedded`
 *   is true, Continuar emits `done` instead of navigating -- changing
 *   locale mid-session must never restart sign-up or consent. */
@Component({
  selector: 'sv-idioma-region',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe],
  templateUrl: './idioma-region.view.html',
  styleUrls: ['../login/login.view.css', './idioma-region.view.css'],
})
export class IdiomaRegionView {
  private readonly router = inject(Router);
  private readonly localeService = inject(LocaleService);

  readonly embedded = input(false);
  readonly done = output<void>();

  protected readonly locales = LOCALES;
  protected readonly selected = this.localeService.locale;
  protected readonly samplePremium = computed(() =>
    formatMoney(SAMPLE_PREMIUM, CURRENCY[this.selected()], this.selected()),
  );
  protected readonly sampleDate = computed(() => formatDate(SAMPLE_DATE, this.selected()));

  protected select(locale: Locale): void {
    this.localeService.use(locale);
  }

  protected continue(): void {
    if (this.embedded()) {
      this.done.emit();
      return;
    }
    // First launch: confirm whatever locale is showing as selected (the
    // default, if the visitor never tapped an option) so requireLocaleChosen
    // on /registro sees a stored choice and does not bounce back here.
    this.localeService.use(this.selected());
    void this.router.navigateByUrl('/registro');
  }
}
