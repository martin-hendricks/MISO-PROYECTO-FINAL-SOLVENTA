import { ChangeDetectionStrategy, Component, inject, input, output } from '@angular/core';
import { Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { Locale, LocaleService, LOCALES } from '../../core/i18n/locale.service';

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
