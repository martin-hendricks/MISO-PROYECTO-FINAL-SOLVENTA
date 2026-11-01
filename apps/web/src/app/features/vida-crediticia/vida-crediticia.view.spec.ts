import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import {
  CATALOGO_VIDA_WIRE,
  FUERA_DE_RANGO,
  OFERTA_HIPOTECARIA_WIRE,
} from '../cotizacion/cotizacion.testing';
import { VidaCrediticiaView } from './vida-crediticia.view';

describe('VidaCrediticiaView', () => {
  const URL = '/web/cliente/oferta-hipotecaria';
  const CATALOGO_URL = '/web/cliente/catalogo/Vida%20crediticia';

  function render() {
    TestBed.configureTestingModule({
      imports: [VidaCrediticiaView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
      ],
    });
    const fixture = TestBed.createComponent(VidaCrediticiaView);
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
    const catalogo = () => {
      http.expectOne(CATALOGO_URL).flush(CATALOGO_VIDA_WIRE);
      fixture.detectChanges();
    };
    const fill = () => {
      type('vida-valorCredito', '180000000');
      type('vida-plazoMeses', '240');
    };
    const autorizar = () => {
      element('vida-autorizar')!.closest('form')!.dispatchEvent(new Event('submit'));
      fixture.detectChanges();
    };
    return { fixture, http, element, type, catalogo, fill, autorizar };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('asks for consent first, with "Ahora no" back to Inicio and no call to the core', () => {
    const { element, catalogo } = render();
    catalogo();

    expect(element('vida-consentimiento')?.textContent).toContain('Autorizas a Solventa');
    expect(element('vida-ahora-no')?.getAttribute('href')).toBe('/inicio');
    expect(element('vida-back')?.getAttribute('href')).toBe('/inicio');
    expect(element<HTMLButtonElement>('vida-autorizar')!.disabled).toBeTrue();
  });

  it('bounds the mortgage data with the catalog ranges', () => {
    const { element, type, catalogo } = render();
    catalogo();

    type('vida-plazoMeses', '400');

    expect(element('vida-plazoMeses-error')?.textContent).toContain('360');
    expect(element<HTMLButtonElement>('vida-autorizar')!.disabled).toBeTrue();
  });

  it('authorizes profiling and shows the offer with its factors, ready to emit', () => {
    const { fixture, http, element, catalogo, fill, autorizar } = render();
    catalogo();
    fill();

    autorizar();
    const request = http.expectOne(URL);
    expect(request.request.body).toEqual({
      credito: { valor: 180000000, plazoMeses: 240 },
      consentimientoPerfil: true,
    });
    request.flush(OFERTA_HIPOTECARIA_WIRE);
    fixture.detectChanges();

    expect(element('oferta-prima')?.textContent).toContain('140.100');
    expect(element('vida-monto')?.textContent).toContain('180.000.000');
    expect(element('vida-plazo')?.textContent).toContain('240 meses');
    expect(element('vida-factor-zona_riesgo')?.textContent).toContain('Zona de riesgo');
    expect(element('vida-factores')?.textContent).toContain('Aumenta la prima');
    expect(element('vida-degradada')).toBeNull();
    expect(element('oferta-aceptar')?.getAttribute('href')).toBe('/emision?cotizacion=COT-7001');
  });

  it('warns when the profile degraded but still offers to emit (HU-56)', () => {
    const { fixture, http, element, catalogo, fill, autorizar } = render();
    catalogo();
    fill();

    autorizar();
    http.expectOne(URL).flush({ ...OFERTA_HIPOTECARIA_WIRE, factores: [], degradada: true });
    fixture.detectChanges();

    expect(element('vida-degradada')).not.toBeNull();
    expect(element('vida-sin-factores')).not.toBeNull();
    expect(element('oferta-aceptar')).not.toBeNull();
  });

  it('shows the core rejection and an outage without leaving the consent step', () => {
    const { fixture, http, element, type, catalogo, fill, autorizar } = render();
    catalogo();
    fill();

    autorizar();
    http.expectOne(URL).flush(FUERA_DE_RANGO, { status: 422, statusText: 'Unprocessable' });
    fixture.detectChanges();
    expect(element('vida-rechazo')).not.toBeNull();

    type('vida-plazoMeses', '120');
    expect(element('vida-rechazo')).toBeNull();

    autorizar();
    http.expectOne(URL).flush(null, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('vida-error')).not.toBeNull();
    expect(element('vida-consentimiento')).not.toBeNull();
  });

  it('lets the customer retry the catalog', () => {
    const { fixture, http, element } = render();
    http.expectOne(CATALOGO_URL).flush(null, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();

    element('vida-catalogo-retry')!.click();
    http.expectOne(CATALOGO_URL).flush(CATALOGO_VIDA_WIRE);
    fixture.detectChanges();

    expect(element('vida-catalogo-error')).toBeNull();
  });

  it('marks an empty field once the customer leaves it, and never submits invalid data', () => {
    const { fixture, http, element, catalogo, autorizar } = render();
    catalogo();

    element('vida-valorCredito')!.dispatchEvent(new Event('blur'));
    fixture.detectChanges();
    autorizar();

    expect(element('vida-valorCredito-error')?.textContent).toContain('Campo obligatorio');
    http.expectNone(URL);
  });

  it('formats the amount in pesos while the catalog is still loading', () => {
    const { element, type, catalogo } = render();

    type('vida-valorCredito', '180000000');

    expect(element('vida-valorCredito')!.parentElement!.textContent).toContain('COP');
    catalogo();
  });

  it('shows a factor without a business name by its code', () => {
    const { fixture, http, element, catalogo, fill, autorizar } = render();
    catalogo();
    fill();

    autorizar();
    http.expectOne(URL).flush({
      ...OFERTA_HIPOTECARIA_WIRE,
      factores: [{ factor: 'factor_nuevo', impacto: 'aumenta_prima' }],
    });
    fixture.detectChanges();

    expect(element('vida-factor-factor_nuevo')?.textContent).toContain('factor_nuevo');
  });
});
