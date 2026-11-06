import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { map } from 'rxjs';
import { TranslatePipe } from '@ngx-translate/core';
import { MoneyPipe } from '../../../core/i18n/format';
import { ConfirmacionTarjetaViewModel } from './confirmacion-tarjeta.viewmodel';

@Component({
  selector: 'sv-confirmacion-tarjeta',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, TranslatePipe, MoneyPipe],
  templateUrl: './confirmacion-tarjeta.view.html',
  styleUrl: './confirmacion-tarjeta.view.css',
})
export class ConfirmacionTarjetaView {
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  protected readonly vm = new ConfirmacionTarjetaViewModel();
  protected readonly cotizacion = toSignal(
    this.route.queryParamMap.pipe(map((params) => params.get('cotizacion') ?? '')),
    { initialValue: this.route.snapshot.queryParamMap.get('cotizacion') ?? '' },
  );
  protected readonly prima = toSignal(
    this.route.queryParamMap.pipe(map((params) => Number(params.get('prima') ?? '0'))),
    { initialValue: Number(this.route.snapshot.queryParamMap.get('prima') ?? '0') },
  );

  protected holder(event: Event): void {
    this.vm.setHolder((event.target as HTMLInputElement).value);
  }

  protected number(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.vm.setNumber(input.value);
    input.value = this.vm.grouped();
  }

  protected month(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.vm.setMonth(input.value);
    input.value = this.vm.month();
  }

  protected year(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.vm.setYear(input.value);
    input.value = this.vm.year();
  }

  protected code(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.vm.setCode(input.value);
    input.value = this.vm.code();
  }

  protected confirm(): void {
    const cotizacion = this.cotizacion();
    if (!cotizacion || !this.vm.ready()) {
      return;
    }
    this.vm.clear();
    void this.router.navigate(['/emision'], { queryParams: { cotizacion } });
  }

  protected leave(): void {
    this.vm.clear();
  }
}
