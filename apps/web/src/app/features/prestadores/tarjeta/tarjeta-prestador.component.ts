import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  HostListener,
  input,
  OnDestroy,
  output,
  viewChild,
} from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { Prestador } from '../prestadores.gateway';
import { enlaceComoLlegar, enlaceLlamada, formatoKm } from '../tipo-prestador';

/** Card over the map for a tapped marker or list row; a stack shows one row per provider. */
@Component({
  selector: 'sv-tarjeta-prestador',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe],
  templateUrl: './tarjeta-prestador.component.html',
  styleUrl: './tarjeta-prestador.component.css',
})
export class TarjetaPrestadorComponent implements AfterViewInit, OnDestroy {
  readonly prestadores = input.required<readonly Prestador[]>();
  readonly referencia = input<'posicion' | 'evento' | null>(null);
  readonly cerrar = output<void>();

  private readonly titulo = viewChild.required<ElementRef<HTMLElement>>('titulo');
  private readonly origenFoco = document.activeElement as HTMLElement;

  protected readonly comoLlegar = enlaceComoLlegar;
  protected readonly llamar = enlaceLlamada;

  @HostListener('document:keydown.escape')
  protected alEscapar(): void {
    this.cerrar.emit();
  }

  ngAfterViewInit(): void {
    this.titulo().nativeElement.focus();
  }

  ngOnDestroy(): void {
    this.origenFoco.focus();
  }

  protected km(prestador: Prestador): string | null {
    return this.referencia() && prestador.distanciaKm !== null
      ? formatoKm(prestador.distanciaKm)
      : null;
  }
}
