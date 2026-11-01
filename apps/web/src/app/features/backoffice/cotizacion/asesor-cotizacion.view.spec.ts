import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import {
  CATALOGO_DISPOSITIVO_WIRE,
  CATALOGO_SOAT_WIRE,
  CATALOGO_VIDA_WIRE,
  OFERTA_HIPOTECARIA_WIRE,
  FUERA_DE_RANGO,
  OFERTA_DESGLOSE_WIRE,
  OFERTA_WIRE,
} from '../../cotizacion/cotizacion.testing';
import { sessionAs } from '../backoffice.testing';
import { AsesorCotizacionView } from './asesor-cotizacion.view';

describe('AsesorCotizacionView', () => {
  const URL = '/web/asesor/cotizaciones';
  const DISPOSITIVO_URL = '/web/asesor/catalogo/Protecci%C3%B3n%20de%20dispositivo';
  const VIGENTE = { ...OFERTA_DESGLOSE_WIRE, venceEn: '2999-01-01T00:00:00Z' };

  function render(role: Role = 'asesor', query: Record<string, string> = {}) {
    TestBed.configureTestingModule({
      imports: [AsesorCotizacionView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: convertToParamMap(query) } },
        },
      ],
    });
    const fixture = TestBed.createComponent(AsesorCotizacionView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    if (role === 'asesor') {
      http.expectOne(DISPOSITIVO_URL).flush(CATALOGO_DISPOSITIVO_WIRE);
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
    const cliente = () => {
      type('cliente-nombre', 'Andrés Gómez');
      type('cliente-documento', '1020334556');
    };
    const fill = () => {
      cliente();
      type('riesgo-valorDispositivo', '2400000');
      choose('riesgo-marca', 'samsung');
      type('riesgo-modelo', 'Galaxy S24');
      element('riesgo-masDe12Meses-si')!.dispatchEvent(new Event('change'));
      fixture.detectChanges();
    };
    const calcular = () => {
      element('calcular')!.closest('form')!.dispatchEvent(new Event('submit'));
      fixture.detectChanges();
    };
    return { fixture, http, element, type, choose, cliente, fill, calcular };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('groups customer and risk data, with the line picker and no plate for devices', () => {
    const { element } = render();

    expect(element('cliente-nombre')).not.toBeNull();
    expect(element<HTMLSelectElement>('cotizacion-ramo')!.value).toBe('dispositivo');
    expect(element('riesgo-placa')).toBeNull();
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
      ramo: 'Protección de dispositivo',
      datosRiesgo: {
        valorDispositivo: 2400000,
        marca: 'samsung',
        modelo: 'Galaxy S24',
        masDe12Meses: true,
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

  it('asks for the plate only on SOAT and keeps the customer data when the line changes', () => {
    const { fixture, http, element, type, choose, cliente, calcular } = render();
    cliente();

    choose('cotizacion-ramo', 'soat');
    http.expectOne('/web/asesor/catalogo/SOAT%20motocicleta').flush(CATALOGO_SOAT_WIRE);
    fixture.detectChanges();
    expect(element<HTMLInputElement>('cliente-nombre')!.value).toBe('Andrés Gómez');
    type('riesgo-placa', 'AB1');
    element('riesgo-placa')!.dispatchEvent(new Event('blur'));
    fixture.detectChanges();
    expect(element('riesgo-placa-error')?.textContent).toContain('ABC12D');

    type('riesgo-placa', 'abc 12d');
    type('riesgo-cilindraje_cc', '150');
    type('riesgo-modelo_anio', '2022');
    choose('riesgo-ciudad_circulacion', 'cali');
    calcular();

    expect(http.expectOne(URL).request.body.datosRiesgo).toEqual({
      cilindraje_cc: 150,
      modelo_anio: 2022,
      ciudad_circulacion: 'cali',
      placa: 'ABC12D',
    });
  });

  it('quotes with the real id of the client opened from Clientes (HU-10)', () => {
    const { fixture, http, element, type, choose, calcular } = render('asesor', {
      cliente: 'CLI-18',
      nombre: 'Andrés Gómez',
      documento: '1020334556',
    });

    expect(element<HTMLInputElement>('cliente-nombre')!.value).toBe('Andrés Gómez');
    expect(element<HTMLInputElement>('cliente-documento')!.value).toBe('1020334556');
    type('riesgo-valorDispositivo', '2400000');
    choose('riesgo-marca', 'apple');
    type('riesgo-modelo', 'iPhone 15');
    element('riesgo-masDe12Meses-no')!.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    calcular();

    const request = http.expectOne(URL);
    expect(request.request.body.clienteId).toBe('CLI-18');
    request.flush(VIGENTE);
    fixture.detectChanges();
    expect(element('continuar-emision')?.getAttribute('href')).toBe(
      '/cms/cotizaciones/COT-4471/emision?cliente=CLI-18',
    );
  });

  it('falls back to the document once the advisor edits a prefilled client', () => {
    const { fixture, http, element, type, choose, calcular } = render('asesor', {
      cliente: 'CLI-18',
      nombre: 'Andrés Gómez',
      documento: '1020334556',
    });

    type('cliente-documento', '52448901');
    type('riesgo-valorDispositivo', '2400000');
    choose('riesgo-marca', 'apple');
    type('riesgo-modelo', 'iPhone 15');
    element('riesgo-masDe12Meses-no')!.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    calcular();

    expect(http.expectOne(URL).request.body.clienteId).toBe('52448901');
  });

  it('prefills only the id when Clientes sends no name or document', () => {
    const { element } = render('asesor', { cliente: 'CLI-18' });

    expect(element<HTMLInputElement>('cliente-nombre')!.value).toBe('');
    expect(element<HTMLInputElement>('cliente-documento')!.value).toBe('');
  });

  it('omits the breakdown when bff-web does not send it', () => {
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

  it('resolves an out of range insured value in this view and degrades to no offer', () => {
    const { fixture, http, element, fill, type, calcular } = render();
    fill();
    calcular();
    http.expectOne(URL).flush(VIGENTE);
    fixture.detectChanges();

    type('riesgo-valorDispositivo', '20000000');

    expect(element('riesgo-valorDispositivo-error')?.textContent).toContain(
      'entre 500000 y 10000000',
    );
    expect(element<HTMLButtonElement>('calcular')!.disabled).toBeTrue();
    expect(element('sin-oferta')).not.toBeNull();
    expect(element<HTMLInputElement>('cliente-nombre')!.value).toBe('Andrés Gómez');
  });

  it('validates customer data before quoting', () => {
    const { fixture, element, type } = render();

    type('cliente-documento', '12ab');
    element('cliente-nombre')!.dispatchEvent(new Event('blur'));
    fixture.detectChanges();

    expect(element('cliente-documento-error')?.textContent).toContain('entre 5 y 12');
    expect(element('cliente-nombre-error')?.textContent).toContain('obligatorio');
    expect(element<HTMLButtonElement>('calcular')!.disabled).toBeTrue();
  });

  it('shows the core rejection and an outage in the offer panel', () => {
    const { fixture, http, element, type, fill, calcular } = render();
    fill();

    calcular();
    http.expectOne(URL).flush(FUERA_DE_RANGO, { status: 422, statusText: 'Unprocessable Entity' });
    fixture.detectChanges();
    expect(element('cotizacion-rechazo')?.textContent).toContain('fuera de rango');

    type('riesgo-valorDispositivo', '2500000');
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

  describe('mortgage life (HU-58)', () => {
    const HIPOTECARIO_URL = '/web/asesor/oferta-hipotecaria';

    function hipotecario() {
      const view = render();
      view.cliente();
      view.choose('cotizacion-ramo', 'hipotecario');
      view.http.expectOne('/web/asesor/catalogo/Vida%20hipotecario').flush(CATALOGO_VIDA_WIRE);
      view.fixture.detectChanges();
      view.type('riesgo-valorCredito', '180000000');
      view.type('riesgo-plazoMeses', '240');
      const consentir = () => {
        const check = view.element<HTMLInputElement>('asesor-consentimiento')!;
        check.checked = true;
        check.dispatchEvent(new Event('change'));
        view.fixture.detectChanges();
      };
      return { ...view, consentir };
    }

    it('quotes only once the customer consents to profiling', () => {
      const { element, consentir } = hipotecario();

      expect(element('asesor-consentimiento')).not.toBeNull();
      expect(element<HTMLButtonElement>('calcular')!.disabled).toBeTrue();

      consentir();

      expect(element<HTMLButtonElement>('calcular')!.disabled).toBeFalse();
    });

    it('shows the same profiled offer the customer sees and continues to issuance', () => {
      const { fixture, http, element, consentir, calcular } = hipotecario();
      consentir();

      calcular();
      const request = http.expectOne(HIPOTECARIO_URL);
      expect(request.request.body).toEqual({
        clienteId: '1020334556',
        credito: { valor: 180000000, plazoMeses: 240 },
        consentimientoPerfil: true,
      });
      request.flush(OFERTA_HIPOTECARIA_WIRE);
      fixture.detectChanges();

      expect(element('oferta-prima')?.textContent).toContain('140.100');
      expect(element('oferta-factores')?.textContent).toContain('Zona de riesgo');
      expect(element('oferta-factores')?.textContent).toContain('Reduce la prima');
      expect(element('oferta-degradada')).toBeNull();
      expect(element('continuar-emision')?.getAttribute('href')).toBe(
        '/cms/cotizaciones/COT-7001/emision?cliente=1020334556',
      );
    });

    it('warns when the profile degraded and names an unknown factor by its code', () => {
      const { fixture, http, element, consentir, calcular } = hipotecario();
      consentir();

      calcular();
      http.expectOne(HIPOTECARIO_URL).flush({
        ...OFERTA_HIPOTECARIA_WIRE,
        degradada: true,
        factores: [{ factor: 'factor_nuevo', impacto: 'reduce_prima' }],
      });
      fixture.detectChanges();

      expect(element('oferta-degradada')).not.toBeNull();
      expect(element('oferta-factores')?.textContent).toContain('factor_nuevo');
    });
  });
});
