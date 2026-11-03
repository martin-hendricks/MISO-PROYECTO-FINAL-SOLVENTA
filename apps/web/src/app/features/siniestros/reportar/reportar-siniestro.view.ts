import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { PolizasGateway } from '../../polizas/polizas.gateway';
import { SiniestrosGateway, Ubicacion } from '../siniestros.gateway';
import { ReportarSiniestroViewModel } from './reportar-siniestro.viewmodel';

/** Permiso JIT: se pide solo cuando el usuario pulsa el botón, nunca al cargar. */
export function ubicacionDelNavegador(
  geo: Geolocation | null = navigator.geolocation,
): Promise<Ubicacion> {
  return new Promise((resolve, reject) => {
    if (!geo) {
      reject(new Error('sin geolocalización'));
      return;
    }
    geo.getCurrentPosition(
      (pos) =>
        resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          precisionM: Math.round(pos.coords.accuracy),
        }),
      reject,
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 },
    );
  });
}

export function hoyLocal(): string {
  const ahora = new Date();
  ahora.setMinutes(ahora.getMinutes() - ahora.getTimezoneOffset());
  return ahora.toISOString().slice(0, 10);
}

@Component({
  selector: 'sv-reportar-siniestro',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, RouterLink],
  templateUrl: './reportar-siniestro.view.html',
  styleUrls: [
    '../../polizas/polizas.page.css',
    '../siniestros.css',
    './reportar-siniestro.view.css',
  ],
})
export class ReportarSiniestroView {
  private readonly siniestros = inject(SiniestrosGateway);
  private readonly polizas = inject(PolizasGateway);

  protected readonly arrastrando = signal(false);
  protected readonly vm = new ReportarSiniestroViewModel({
    polizas: () => this.polizas.list(),
    enviar: (aviso, clave) => this.siniestros.report(aviso, clave),
    ubicar: () => ubicacionDelNavegador(),
    hoy: hoyLocal,
    nuevaClave: () => crypto.randomUUID(),
  });

  constructor() {
    this.vm.cargarPolizas();
  }

  protected alElegir(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.vm.elegirArchivo(input.files?.item(0) ?? null);
  }

  protected alSoltar(event: DragEvent): void {
    event.preventDefault();
    this.arrastrando.set(false);
    this.vm.elegirArchivo(event.dataTransfer?.files.item(0) ?? null);
  }

  protected alArrastrar(event: DragEvent): void {
    event.preventDefault();
    this.arrastrando.set(true);
  }
}
