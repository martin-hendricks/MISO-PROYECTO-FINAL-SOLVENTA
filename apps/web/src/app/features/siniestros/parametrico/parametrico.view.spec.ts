import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { ParametricoView } from './parametrico.view';

describe('ParametricoView', () => {
  it('shows the payout and saves renewal on the related policy only', () => {
    TestBed.configureTestingModule({
      imports: [ParametricoView],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting(), ...provideSolventaI18n()],
    });
    const fixture = TestBed.createComponent(ParametricoView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const pago = http.expectOne('/web/cliente/pagos-automaticos');
    pago.flush({
      siniestroId: 'SIN-220',
      poliza: 'POL-77310',
      umbral: '≥ 80 mm / 24 h',
      monto: 1200000,
      moneda: 'COP',
      estado: 'pagado',
    });
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    expect(host.textContent).toContain('POL-77310');
    expect(host.textContent).toContain('80 mm');
    expect(host.textContent).toContain('1.200.000');
    expect(host.textContent).toContain('Apagado. Opta esa póliza a renovar su prima.');
    const checkbox = host.querySelector<HTMLInputElement>('[data-testid="parametrico-renovacion"]')!;
    checkbox.checked = true;
    checkbox.dispatchEvent(new Event('change'));
    const preference = http.expectOne('/web/cliente/polizas/POL-77310/preferencias');
    expect(preference.request.method).toBe('PATCH');
    expect(preference.request.body).toEqual({ renovacionAutomatica: true });
    preference.flush({ numero: 'POL-77310', renovacionAutomatica: true });
    fixture.detectChanges();
    expect(host.querySelector('[data-testid="parametrico-renovacion-ayuda"]')).toBeNull();
    http.verify();
  });
});
