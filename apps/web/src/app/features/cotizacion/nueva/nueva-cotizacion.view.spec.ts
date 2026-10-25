import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { FUERA_DE_RANGO, OFERTA_WIRE } from '../cotizacion.testing';
import { NuevaCotizacionView } from './nueva-cotizacion.view';

describe('NuevaCotizacionView', () => {
  const URL = '/web/cliente/cotizaciones';

  function render() {
    TestBed.configureTestingModule({
      imports: [NuevaCotizacionView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
      ],
    });
    const navigate = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(NuevaCotizacionView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = <T extends HTMLElement = HTMLElement>(testId: string) =>
      host.querySelector<T>(`[data-testid="${testId}"]`);
    const type = (testId: string, value: string) => {
      const input = element<HTMLInputElement>(testId)!;
      input.value = value;
      input.dispatchEvent(new Event('input'));
      fixture.detectChanges();
    };
    const fill = () => {
      type('riesgo-cilindraje_cc', '150');
      type('riesgo-modelo_anio', '2022');
      const ciudad = element<HTMLSelectElement>('riesgo-ciudad_circulacion')!;
      ciudad.value = 'cali';
      ciudad.dispatchEvent(new Event('change'));
      fixture.detectChanges();
    };
    const cotizar = () => {
      element('cotizar')!.closest('form')!.dispatchEvent(new Event('submit'));
      fixture.detectChanges();
    };
    return { fixture, http, element, type, fill, cotizar, navigate };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('locks the product to the single line of business', () => {
    const { element } = render();

    const producto = element<HTMLInputElement>('cotizacion-producto')!;
    expect(producto.value).toBe('SOAT motocicleta');
    expect(producto.readOnly).toBeTrue();
  });

  it('quotes and opens the offer by its id', () => {
    const { http, fill, cotizar, navigate } = render();
    fill();

    cotizar();

    const request = http.expectOne(URL);
    expect(request.request.body).toEqual({
      ramo: 'SOAT motocicleta',
      datosRiesgo: { cilindraje_cc: 150, modelo_anio: 2022, ciudad_circulacion: 'cali' },
    });
    request.flush(OFERTA_WIRE);
    expect(navigate).toHaveBeenCalledOnceWith(['/cotizaciones', 'COT-4471']);
  });

  it('marks an out of range value with its valid range and keeps "Cotizar" disabled', () => {
    const { http, element, fill, type, cotizar } = render();
    fill();

    type('riesgo-cilindraje_cc', '2500');
    cotizar();

    http.expectNone(URL);
    expect(element('riesgo-cilindraje_cc-error')?.textContent).toContain('entre 50 y 1800');
    expect(element('riesgo-cilindraje_cc')?.getAttribute('aria-invalid')).toBe('true');
    expect(element<HTMLButtonElement>('cotizar')!.disabled).toBeTrue();
    expect(element<HTMLInputElement>('riesgo-cilindraje_cc')!.value).toBe('2500');
  });

  it('shows the valid range as a hint and flags an empty field once left', () => {
    const { fixture, element } = render();

    expect(element('riesgo-modelo_anio')?.nextElementSibling?.textContent).toContain(
      'Entre 2000 y 2026',
    );
    element('riesgo-modelo_anio')!.dispatchEvent(new Event('blur'));
    fixture.detectChanges();
    expect(element('riesgo-modelo_anio-error')?.textContent).toContain('Campo obligatorio');
  });

  it('shows the core rejection in place without leaving the form (HU-3)', () => {
    const { fixture, http, element, fill, cotizar, navigate } = render();
    fill();

    cotizar();
    http.expectOne(URL).flush(FUERA_DE_RANGO, { status: 422, statusText: 'Unprocessable Entity' });
    fixture.detectChanges();

    expect(element('cotizacion-rechazo')?.textContent).toContain('fuera de rango');
    expect(element('riesgo-cilindraje_cc-error')).not.toBeNull();
    expect(navigate).not.toHaveBeenCalled();
  });

  it('tells an outage apart from invalid data', () => {
    const { fixture, http, element, fill, cotizar } = render();
    fill();

    cotizar();
    http.expectOne(URL).flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();

    expect(element('cotizacion-error')).not.toBeNull();
    expect(element('cotizacion-rechazo')).toBeNull();
  });

  it('returns to Inicio on cancel', () => {
    const { element } = render();

    expect(element('cancelar')?.getAttribute('href')).toBe('/inicio');
  });
});
