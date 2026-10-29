import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { OFERTA_DESGLOSE_WIRE, OFERTA_WIRE } from '../cotizacion.testing';
import { VerOfertaView } from './ver-oferta.view';

describe('VerOfertaView', () => {
  const URL = '/web/cliente/cotizaciones/COT-4471';
  const VIGENTE = { ...OFERTA_WIRE, venceEn: '2999-06-01T12:00:00Z' };

  function render() {
    TestBed.configureTestingModule({
      imports: [VerOfertaView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ cotizacionId: 'COT-4471' }) } },
        },
      ],
    });
    const fixture = TestBed.createComponent(VerOfertaView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('reconsults the offer by id and shows premium, currency and expiry', () => {
    const { fixture, http, element } = render();

    expect(element('oferta-loading')).not.toBeNull();
    const request = http.expectOne(URL);
    expect(request.request.method).toBe('GET');
    request.flush(VIGENTE);
    fixture.detectChanges();

    expect(element('oferta-prima')?.textContent).toContain('128.500');
    expect(element('oferta-moneda')?.textContent).toContain('COP');
    expect(element('oferta-vence')?.textContent).toContain('2999');
    expect(element('oferta-vigencia')?.textContent).toContain('1 año');
    expect(element('oferta-prima-neta')).toBeNull();
    expect(element('oferta-expedicion')).toBeNull();
  });

  it('shows the premium breakdown when the core sends it, like the advisor offer', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush({ ...OFERTA_DESGLOSE_WIRE, venceEn: VIGENTE.venceEn });
    fixture.detectChanges();

    expect(element('oferta-prima-neta')?.textContent).toContain('120.000');
    expect(element('oferta-expedicion')?.textContent).toContain('8.500');
  });

  it('accepts by starting the issuance with the quote id (HU-114)', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush(VIGENTE);
    fixture.detectChanges();

    expect(element('oferta-aceptar')?.getAttribute('href')).toBe('/emision?cotizacion=COT-4471');
  });

  it('keeps the original price of an expired offer and does not let it be accepted', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush({ ...OFERTA_WIRE, venceEn: '2000-01-01T00:00:00Z' });
    fixture.detectChanges();

    expect(element('oferta-prima')?.textContent).toContain('128.500');
    expect(element('oferta-vencida')).not.toBeNull();
    expect(element('oferta-aceptar')).toBeNull();
    expect(element('oferta-nueva')?.getAttribute('href')).toBe('/cotizacion');
  });

  it('shows a not found state for an unknown quote', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush({}, { status: 404, statusText: 'Not Found' });
    fixture.detectChanges();

    expect(element('oferta-not-found')).not.toBeNull();
  });

  it('retries after an outage', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    element('oferta-retry')!.click();
    http.expectOne(URL).flush(VIGENTE);
    fixture.detectChanges();

    expect(element('oferta')).not.toBeNull();
  });
});
