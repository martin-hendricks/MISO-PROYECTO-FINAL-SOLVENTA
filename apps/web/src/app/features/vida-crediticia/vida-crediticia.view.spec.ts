import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import {
  CATALOGO_VIDA_HIPOTECARIO_WIRE,
  FUERA_DE_RANGO,
  OFERTA_HIPOTECARIA_WIRE,
} from '../cotizacion/cotizacion.testing';
import { Credito, VIDA_ETAPA_MS } from './vida-crediticia.gateway';
import { VidaCrediticiaView } from './vida-crediticia.view';

describe('VidaCrediticiaView', () => {
  const URL = '/web/cliente/oferta-hipotecaria';
  const CATALOGO_URL = '/web/cliente/catalogo/Vida%20hipotecario';
  const ORIGINACION_URL = '/web/cliente/originacion-hipotecaria';

  function render(opciones: { originacion?: Credito | null; query?: Record<string, string> } = {}) {
    const query = opciones.query ?? {};
    TestBed.configureTestingModule({
      imports: [VidaCrediticiaView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        { provide: VIDA_ETAPA_MS, useValue: 0 },
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: convertToParamMap(query) } } },
      ],
    });
    const fixture = TestBed.createComponent(VidaCrediticiaView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    if (!('valor' in query)) {
      const originacion = http.expectOne(ORIGINACION_URL);
      if (opciones.originacion) {
        originacion.flush(opciones.originacion);
      } else {
        originacion.flush(null, { status: 404, statusText: 'Not Found' });
      }
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
    const catalogo = () => {
      http.expectOne(CATALOGO_URL).flush(CATALOGO_VIDA_HIPOTECARIO_WIRE);
      fixture.detectChanges();
    };
    const fill = () => {
      type('vida-valor', '180000000');
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
    expect(element('oferta-aceptar')?.getAttribute('href')).toBe(
      '/confirmacion-tarjeta?cotizacion=COT-7001&prima=140100',
    );
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
    http.expectOne(CATALOGO_URL).flush(CATALOGO_VIDA_HIPOTECARIO_WIRE);
    fixture.detectChanges();

    expect(element('vida-catalogo-error')).toBeNull();
  });

  it('marks an empty field once the customer leaves it, and never submits invalid data', () => {
    const { fixture, http, element, catalogo, autorizar } = render();
    catalogo();

    element('vida-valor')!.dispatchEvent(new Event('blur'));
    fixture.detectChanges();
    autorizar();

    expect(element('vida-valor-error')?.textContent).toContain('Campo obligatorio');
    http.expectNone(URL);
  });

  it('formats the amount in pesos while the catalog is still loading', () => {
    const { element, type, catalogo } = render();

    type('vida-valor', '180000000');

    expect(element('vida-valor')!.parentElement!.textContent).toContain('COP');
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

  it('names the competitive adjustment in business terms', () => {
    const { fixture, http, element, catalogo, fill, autorizar } = render();
    catalogo();
    fill();

    autorizar();
    http.expectOne(URL).flush({
      ...OFERTA_HIPOTECARIA_WIRE,
      factores: [{ factor: 'ajuste_competitivo', impacto: 'reduce_prima' }],
    });
    fixture.detectChanges();

    expect(element('vida-factor-ajuste_competitivo')?.textContent).toContain(
      'Ajustada al precio de mercado',
    );
  });

  it('fills the mortgage the customer or a partner left pending and enables "Autorizar"', () => {
    const { element, catalogo } = render({ originacion: { valor: 250000000, plazoMeses: 300 } });
    catalogo();

    expect(element<HTMLInputElement>('vida-valor')!.value).toBe('250000000');
    expect(element<HTMLInputElement>('vida-plazoMeses')!.value).toBe('300');
    expect(element<HTMLButtonElement>('vida-autorizar')!.disabled).toBeFalse();
  });

  it('does not let the customer change a pending mortgage', () => {
    const { http, element, type, catalogo, autorizar } = render({
      originacion: { valor: 250000000, plazoMeses: 300 },
    });
    catalogo();

    expect(element<HTMLInputElement>('vida-valor')!.readOnly).toBeTrue();
    expect(element<HTMLInputElement>('vida-plazoMeses')!.readOnly).toBeTrue();
    type('vida-plazoMeses', '120');
    autorizar();

    expect(http.expectOne(URL).request.body).toEqual({
      credito: { valor: 250000000, plazoMeses: 300 },
      consentimientoPerfil: true,
    });
  });

  it('keeps the mortgage editable when nothing is pending', () => {
    const { element, catalogo } = render();
    catalogo();

    expect(element<HTMLInputElement>('vida-valor')!.readOnly).toBeFalse();
  });

  it('fills the mortgage sent by Nueva cotización without asking the core again', () => {
    const { http, element, catalogo } = render({ query: { valor: '180000000', plazoMeses: '240' } });
    catalogo();

    expect(element<HTMLInputElement>('vida-valor')!.value).toBe('180000000');
    expect(element<HTMLInputElement>('vida-plazoMeses')!.value).toBe('240');
    expect(element<HTMLInputElement>('vida-valor')!.readOnly).toBeTrue();
    http.expectNone(ORIGINACION_URL);
  });

  it('ignores an incomplete mortgage in the address and loads the pending one', () => {
    const { element, catalogo } = render({ query: { plazoMeses: '240' } });
    catalogo();

    expect(element<HTMLInputElement>('vida-valor')!.value).toBe('');
  });

  it('shows each profiling step while Solventa builds the offer', () => {
    const { fixture, http, element, catalogo, fill, autorizar } = render();
    catalogo();
    fill();

    autorizar();

    expect(element('vida-progreso')).not.toBeNull();
    expect(element('vida-etapa-openFinance')?.getAttribute('data-state')).toBe('active');
    expect(element('vida-etapa-openData')?.getAttribute('data-state')).toBe('pending');
    expect(element('vida-etapa-riesgo')?.textContent).toContain('Calculando tu riesgo individualizado');
    expect(element('vida-etapa-oferta')?.textContent).toContain('Generando tu oferta');
    http.expectOne(URL).flush(OFERTA_HIPOTECARIA_WIRE);
    fixture.detectChanges();
    expect(element('vida-progreso')).toBeNull();
  });
});

describe('VIDA_ETAPA_MS', () => {
  it('keeps each profiling step on screen for 700 ms unless told otherwise', () => {
    expect(TestBed.inject(VIDA_ETAPA_MS)).toBe(700);
  });
});
