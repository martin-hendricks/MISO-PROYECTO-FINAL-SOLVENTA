import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import {
  CATALOGO_DISPOSITIVO_WIRE,
  CATALOGO_SOAT_WIRE,
  FUERA_DE_RANGO,
  OFERTA_WIRE,
} from '../cotizacion.testing';
import { NuevaCotizacionView } from './nueva-cotizacion.view';

describe('NuevaCotizacionView', () => {
  const URL = '/web/cliente/cotizaciones';
  const CATALOGO_URL = '/web/cliente/catalogo/Protecci%C3%B3n%20de%20dispositivo';

  function render(catalogo: object | null = CATALOGO_DISPOSITIVO_WIRE) {
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
    if (catalogo) {
      http.expectOne(CATALOGO_URL).flush(catalogo);
      fixture.detectChanges();
    }
    const host = fixture.nativeElement as HTMLElement;
    const element = <T extends HTMLElement = HTMLElement>(testId: string) =>
      host.querySelector<T>(`[data-testid="${testId}"]`);
    const type = (testId: string, value: string) => {
      const input = element<HTMLInputElement>(testId)!;
      input.value = value;
      input.dispatchEvent(new Event('input'));
      fixture.detectChanges();
    };
    const choose = (testId: string, value: string) => {
      const select = element<HTMLSelectElement>(testId)!;
      select.value = value;
      select.dispatchEvent(new Event('change'));
      fixture.detectChanges();
    };
    const fill = () => {
      type('riesgo-valorDispositivo', '2400000');
      choose('riesgo-marca', 'apple');
      type('riesgo-modelo', 'iPhone 15');
      element('riesgo-masDe12Meses-no')!.dispatchEvent(new Event('change'));
      fixture.detectChanges();
    };
    const cotizar = () => {
      element('cotizar')!.closest('form')!.dispatchEvent(new Event('submit'));
      fixture.detectChanges();
    };
    return { fixture, http, element, type, choose, fill, cotizar, navigate };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('offers the seven lines and disables the ones the core does not quote yet', () => {
    const { element } = render();

    const options = Array.from(element<HTMLSelectElement>('cotizacion-ramo')!.options);
    expect(options.map((o) => [o.textContent!.replace(/\s+/g, ' ').trim(), o.disabled])).toEqual([
      ['Protección de dispositivo', false],
      ['SOAT motocicleta', false],
      ['Microseguro de vida · Próximamente', true],
      ['Clima y vuelos · Próximamente', true],
      ['Vida hipotecario · Próximamente', true],
      ['Pagos · Próximamente', true],
      ['Viaje · Próximamente', true],
    ]);
  });

  it('shows the device form with the coverages and brands of the catalog', () => {
    const { element } = render();

    expect(element('coberturas')?.textContent?.replace(/\s+/g, ' ')).toContain(
      'Robo · Daño accidental · Reposición por equipo nuevo',
    );
    const marcas = Array.from(element<HTMLSelectElement>('riesgo-marca')!.options).map((o) =>
      o.textContent!.trim(),
    );
    expect(marcas).toEqual(['Selecciona una opción', 'Samsung', 'Apple', 'Xiaomi', 'Motorola']);
    expect(element('riesgo-modelo')).not.toBeNull();
    expect(element('riesgo-masDe12Meses-si')).not.toBeNull();
  });

  it('quotes the device and opens the offer by its id', () => {
    const { http, element, fill, cotizar, navigate } = render();
    fill();

    expect(element('riesgo-valorDispositivo-monto')?.textContent).toContain('2.400.000');
    cotizar();

    const request = http.expectOne(URL);
    expect(request.request.body).toEqual({
      ramo: 'Protección de dispositivo',
      datosRiesgo: {
        valorDispositivo: 2400000,
        marca: 'apple',
        modelo: 'iPhone 15',
        masDe12Meses: false,
      },
    });
    request.flush(OFERTA_WIRE);
    expect(navigate).toHaveBeenCalledOnceWith(['/cotizaciones', 'COT-4471']);
  });

  it('blocks "Cotizar" with an insured value out of range and keeps what was typed', () => {
    const { http, element, fill, type, cotizar } = render();
    fill();

    type('riesgo-valorDispositivo', '20000000');
    cotizar();

    http.expectNone(URL);
    expect(element('riesgo-valorDispositivo-error')?.textContent).toContain(
      'entre 500000 y 10000000',
    );
    expect(element('riesgo-valorDispositivo')?.getAttribute('aria-invalid')).toBe('true');
    expect(element<HTMLButtonElement>('cotizar')!.disabled).toBeTrue();
    expect(element<HTMLInputElement>('riesgo-modelo')!.value).toBe('iPhone 15');
  });

  it('switches to SOAT and shows its own fields and range hints', () => {
    const { fixture, http, element, choose } = render();

    choose('cotizacion-ramo', 'soat');
    http.expectOne('/web/cliente/catalogo/SOAT%20motocicleta').flush(CATALOGO_SOAT_WIRE);
    fixture.detectChanges();

    expect(element('riesgo-valorDispositivo')).toBeNull();
    expect(element('riesgo-cilindraje_cc')?.nextElementSibling?.textContent).toContain(
      'Entre 50 y 1800',
    );
    const ciudades = Array.from(
      element<HTMLSelectElement>('riesgo-ciudad_circulacion')!.options,
    ).map((o) => o.textContent!.trim());
    expect(ciudades).toEqual(['Selecciona una opción', 'Bogotá', 'Medellín', 'Cali']);
  });

  it('flags an empty field once left and a positive number rule', () => {
    const { fixture, element, type } = render();

    element('riesgo-modelo')!.dispatchEvent(new Event('blur'));
    element('riesgo-marca')!.dispatchEvent(new Event('blur'));
    fixture.detectChanges();
    type('riesgo-valorDispositivo', '0');

    expect(element('riesgo-modelo-error')?.textContent).toContain('Campo obligatorio');
    expect(element('riesgo-marca-error')?.textContent).toContain('Campo obligatorio');
    expect(element('riesgo-valorDispositivo-error')?.textContent).toContain('mayor que cero');
  });

  it('shows the core rejection in place without leaving the form (HU-3)', () => {
    const { fixture, http, element, fill, cotizar, navigate } = render();
    fill();

    cotizar();
    http.expectOne(URL).flush(FUERA_DE_RANGO, { status: 422, statusText: 'Unprocessable Entity' });
    fixture.detectChanges();

    expect(element('cotizacion-rechazo')?.textContent).toContain('fuera de rango');
    expect(element('riesgo-valorDispositivo-error')).not.toBeNull();
    expect(navigate).not.toHaveBeenCalled();
  });

  it('marks a field the core rejects even when the catalog has no range for it', () => {
    const sinRangos = {
      ...CATALOGO_DISPOSITIVO_WIRE,
      datosRiesgo: CATALOGO_DISPOSITIVO_WIRE.datosRiesgo.slice(1),
      coberturas: [],
    };
    const { fixture, http, element, fill, cotizar } = render(sinRangos);
    fill();
    cotizar();
    http.expectOne(URL).flush(FUERA_DE_RANGO, { status: 422, statusText: 'Unprocessable Entity' });
    fixture.detectChanges();

    expect(element('coberturas')).toBeNull();
    expect(element('riesgo-valorDispositivo-error')?.textContent).toContain(
      'Fuera del rango permitido',
    );
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

  it('blocks "Cotizar" when the catalog fails and retries it', () => {
    const { fixture, http, element } = render(null);

    http.expectOne(CATALOGO_URL).flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('catalogo-error')).not.toBeNull();
    expect(element<HTMLButtonElement>('cotizar')!.disabled).toBeTrue();

    element('catalogo-retry')!.click();
    http.expectOne(CATALOGO_URL).flush(CATALOGO_DISPOSITIVO_WIRE);
    fixture.detectChanges();
    expect(element('catalogo-error')).toBeNull();
  });

  it('returns to Inicio on cancel', () => {
    const { element } = render();

    expect(element('cancelar')?.getAttribute('href')).toBe('/inicio');
  });
  it('shows a catalog value without a translation as the core sends it', () => {
    const conHuawei = {
      ...CATALOGO_DISPOSITIVO_WIRE,
      datosRiesgo: [{ nombre: 'marca', tipo: 'valores', valores: ['huawei'] }],
    };
    const { element } = render(conHuawei);

    const marcas = Array.from(element<HTMLSelectElement>('riesgo-marca')!.options);
    expect(marcas.map((o) => o.textContent!.trim())).toEqual(['Selecciona una opción', 'huawei']);
  });
});
