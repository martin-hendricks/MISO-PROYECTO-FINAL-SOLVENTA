import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import {
  CATALOGO_WIRE,
  FUERA_DE_RANGO,
  OFERTA_DESGLOSE_WIRE,
  OFERTA_WIRE,
} from '../../cotizacion/cotizacion.testing';
import { sessionAs } from '../backoffice.testing';
import { AsesorCotizacionView } from './asesor-cotizacion.view';

describe('AsesorCotizacionView', () => {
  const URL = '/web/asesor/cotizaciones';
  const VIGENTE = { ...OFERTA_DESGLOSE_WIRE, venceEn: '2999-01-01T00:00:00Z' };

  function render(role: Role = 'asesor') {
    TestBed.configureTestingModule({
      imports: [AsesorCotizacionView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
      ],
    });
    const fixture = TestBed.createComponent(AsesorCotizacionView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    if (role === 'asesor') {
      http.expectOne('/web/asesor/catalogo/SOAT%20motocicleta').flush(CATALOGO_WIRE);
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
    const fill = () => {
      type('cliente-nombre', 'Andrés Gómez');
      type('cliente-documento', '1020334556');
      type('riesgo-placa', 'abc 12d');
      type('riesgo-cilindraje_cc', '150');
      type('riesgo-modelo_anio', '2022');
    };
    const calcular = () => {
      element('calcular')!.closest('form')!.dispatchEvent(new Event('submit'));
      fixture.detectChanges();
    };
    return { fixture, http, element, type, fill, calcular };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('groups the form in customer and risk data with the product locked', () => {
    const { element } = render();

    expect(element<HTMLInputElement>('cotizacion-producto')!.value).toBe('SOAT motocicleta');
    expect(element('cliente-nombre')).not.toBeNull();
    expect(element('riesgo-placa')).not.toBeNull();
    expect(element('sin-oferta')).not.toBeNull();
    expect(element<HTMLButtonElement>('calcular')!.disabled).toBeTrue();
    expect(element('cotizacion-back')?.getAttribute('href')).toBe('/cms/cotizaciones');
  });

  it('quotes on behalf of the customer and fills the offer panel', () => {
    const { fixture, http, element, fill, calcular } = render();
    fill();

    calcular();
    expect(element('oferta-calculando')).not.toBeNull();
    const request = http.expectOne(URL);
    expect(request.request.body).toEqual({
      clienteId: '1020334556',
      ramo: 'SOAT motocicleta',
      datosRiesgo: {
        cilindraje_cc: 150,
        modelo_anio: 2022,
        ciudad_circulacion: 'bogota',
        placa: 'ABC12D',
      },
    });
    request.flush(VIGENTE);
    fixture.detectChanges();

    expect(element('sin-oferta')).toBeNull();
    expect(element('oferta-prima')?.textContent).toContain('128.500');
    expect(element('oferta-prima-neta')?.textContent).toContain('120.000');
    expect(element('oferta-expedicion')?.textContent).toContain('8.500');
    expect(element('oferta-id')?.textContent).toContain('COT-4471');
    expect(element('continuar-emision')?.getAttribute('href')).toBe(
      '/cms/cotizaciones/COT-4471/emision?cliente=1020334556',
    );
  });

  it('omits the breakdown until bff-web sends it', () => {
    const { fixture, http, element, fill, calcular } = render();
    fill();

    calcular();
    http.expectOne(URL).flush({ ...OFERTA_WIRE, venceEn: '2999-01-01T00:00:00Z' });
    fixture.detectChanges();

    expect(element('oferta-prima')).not.toBeNull();
    expect(element('oferta-prima-neta')).toBeNull();
    expect(element('oferta-expedicion')).toBeNull();
  });

  it('does not continue to issuance with an expired offer', () => {
    const { fixture, http, element, fill, calcular } = render();
    fill();

    calcular();
    http.expectOne(URL).flush({ ...OFERTA_WIRE, venceEn: '2000-01-01T00:00:00Z' });
    fixture.detectChanges();

    expect(element('continuar-emision')).toBeNull();
    expect(element('oferta-vencida')).not.toBeNull();
  });

  it('resolves an out of range value in this view and degrades to no offer', () => {
    const { fixture, http, element, fill, type, calcular } = render();
    fill();
    calcular();
    http.expectOne(URL).flush(VIGENTE);
    fixture.detectChanges();

    type('riesgo-cilindraje_cc', '2500');

    expect(element('riesgo-cilindraje_cc-error')?.textContent).toContain('entre 50 y 1800');
    expect(element<HTMLButtonElement>('calcular')!.disabled).toBeTrue();
    expect(element('sin-oferta')).not.toBeNull();
    expect(element<HTMLInputElement>('cliente-nombre')!.value).toBe('Andrés Gómez');
  });

  it('validates customer data and plate before quoting', () => {
    const { fixture, element, type } = render();

    type('cliente-documento', '12ab');
    type('riesgo-placa', 'AB1');
    element('cliente-nombre')!.dispatchEvent(new Event('blur'));
    element('riesgo-placa')!.dispatchEvent(new Event('blur'));
    fixture.detectChanges();

    expect(element('cliente-documento-error')?.textContent).toContain('entre 5 y 12');
    expect(element('riesgo-placa-error')?.textContent).toContain('ABC12D');
    expect(element('cliente-nombre-error')?.textContent).toContain('obligatorio');
    expect(element<HTMLButtonElement>('calcular')!.disabled).toBeTrue();
  });

  it('shows the core rejection and an outage in the offer panel', () => {
    const { fixture, http, element, fill, calcular } = render();
    fill();

    calcular();
    http.expectOne(URL).flush(FUERA_DE_RANGO, { status: 422, statusText: 'Unprocessable Entity' });
    fixture.detectChanges();
    expect(element('cotizacion-rechazo')?.textContent).toContain('fuera de rango');

    element<HTMLInputElement>('riesgo-cilindraje_cc')!.value = '160';
    element('riesgo-cilindraje_cc')!.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    calcular();
    http.expectOne(URL).flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('cotizacion-error')).not.toBeNull();
  });

  it('keeps the quote from the operator without calling the BFF', () => {
    const { http, element } = render('operador');

    http.expectNone(URL);
    expect(element('asesor-cotizacion')?.getAttribute('data-state')).toBe('no-permission');
    expect(element('calcular')).toBeNull();
  });
});
