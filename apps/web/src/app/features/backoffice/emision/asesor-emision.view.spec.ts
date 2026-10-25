import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { APROBADA, EMITIDA, RECHAZADA } from './asesor-emision.testing';
import { AsesorEmisionView } from './asesor-emision.view';

describe('AsesorEmisionView', () => {
  const URL = '/web/asesor/emisiones';
  const ISSUE_URL = '/web/asesor/emisiones/SOL-0091/poliza';

  function render(role: Role = 'asesor', query: Record<string, string> = {}) {
    TestBed.configureTestingModule({
      imports: [AsesorEmisionView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ cotizacionId: 'COT-4471' }),
              queryParamMap: convertToParamMap({
                cliente: 'CLI-18',
                ...query,
              }),
            },
          },
        },
      ],
    });
    const fixture = TestBed.createComponent(AsesorEmisionView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    const steps = () =>
      Array.from(host.querySelectorAll<HTMLElement>('[data-testid="stepper"] li')).map(
        (li) => `${li.dataset['paso']}:${li.dataset['estado']}`,
      );
    return { fixture, http, host, element, steps };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('asks the core for the decision of the accepted offer', () => {
    const { http, element } = render();

    const request = http.expectOne(URL);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      cotizacionId: 'COT-4471',
      clienteId: 'CLI-18',
    });
    expect(element('emision-loading')).not.toBeNull();
    request.flush(APROBADA);
  });

  it('shows the approved decision, the offer summary and the real core steps', () => {
    const { fixture, http, element, steps } = render();

    http.expectOne(URL).flush(APROBADA);
    fixture.detectChanges();

    expect(element('emision-context')?.textContent).toContain('Andrés Gómez Molina');
    expect(element('emision-context')?.textContent).toContain('SOAT motocicleta');
    expect(steps()).toEqual([
      'COTIZAR:COMPLETADO',
      'OFERTA:COMPLETADO',
      'EMISION:ACTUAL',
      'POLIZA:PENDIENTE',
    ]);
    expect(element('decision-badge')?.textContent?.trim()).toBe('Aprobada');
    const decision = element('decision')!.textContent!;
    expect(decision).toContain('Dentro de apetito de riesgo');
    expect(decision).toContain('A · sin siniestralidad previa');
    expect(decision).toContain('Motor automático');
    expect(decision).toContain('16/09/2026');
    const resumen = element('resumen-oferta')!.textContent!;
    expect(resumen).toContain('148.900');
    expect(resumen).toContain('132.400');
    expect(resumen).toContain('16.500');
    expect(resumen).toContain('12');
    expect(element('emitir')).not.toBeNull();
    expect(element('guardar-salir')?.getAttribute('href')).toBe('/cms/cotizaciones');
    expect(element('poliza-emitida')).toBeNull();
  });

  it('signs and issues the policy, keeping the offer summary', () => {
    const { fixture, http, element, steps } = render();
    http.expectOne(URL).flush(APROBADA);
    fixture.detectChanges();

    element('emitir')!.click();
    fixture.detectChanges();
    expect(element('emision-issuing')).not.toBeNull();
    expect(element('emitir')).toBeNull();
    const request = http.expectOne(ISSUE_URL);
    expect(request.request.method).toBe('POST');
    request.flush(EMITIDA);
    fixture.detectChanges();

    expect(steps()).toEqual([
      'COTIZAR:COMPLETADO',
      'OFERTA:COMPLETADO',
      'EMISION:COMPLETADO',
      'POLIZA:COMPLETADO',
    ]);
    expect(element('poliza-emitida')?.textContent).toContain('POL-2026-00090102');
    expect(element('poliza-emitida')?.textContent).toContain('16/09/2027');
    expect(element('resumen-oferta')?.textContent).toContain('148.900');
    expect(element('emitir')).toBeNull();
  });

  it('marks the issuance step as an error and never shows an issued policy when the core rejects', () => {
    const { fixture, http, host, element, steps } = render();

    http.expectOne(URL).flush(RECHAZADA);
    fixture.detectChanges();

    expect(steps()[2]).toBe('EMISION:ERROR');
    expect(element('decision-badge')?.textContent?.trim()).toBe('Rechazada');
    expect(element('decision')?.textContent).toContain('1.400 cc supera el máximo de 1.200 cc');
    expect(element('rechazo')).not.toBeNull();
    expect(element('emitir')).toBeNull();
    expect(element('poliza-emitida')).toBeNull();
    expect(host.textContent).not.toMatch(/emitida/i);
  });

  it('lets the advisor quote another product for the same customer or go back to the portfolio', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(RECHAZADA);
    fixture.detectChanges();

    expect(element('cotizar-otro')?.getAttribute('href')).toBe('/cms/cotizaciones?cliente=CLI-18');
    expect(element('volver-cartera')?.getAttribute('href')).toBe('/cms/clientes');
  });

  it('goes back to the quote', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(APROBADA);
    fixture.detectChanges();

    expect(element('emision-back')?.textContent).toContain('COT-4471');
    expect(element('emision-back')?.getAttribute('href')).toBe('/cms/cotizaciones');
  });

  it('offers to retry when the issuance fails', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(APROBADA);
    fixture.detectChanges();
    element('emitir')!.click();
    http.expectOne(ISSUE_URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    expect(element('emision-error')).not.toBeNull();
    element('emision-retry')!.click();
    http.expectOne(ISSUE_URL).flush(EMITIDA);
    fixture.detectChanges();

    expect(element('emision-error')).toBeNull();
    expect(element('poliza-emitida')).not.toBeNull();
  });

  it('does not call the BFF without the customer it serves', () => {
    const { http, element } = render('asesor', { cliente: '' });

    http.expectNone(URL);
    expect(element('emision-invalid')).not.toBeNull();
  });

  it('keeps the issuance from the operator without calling the BFF', () => {
    const { http, element } = render('operador');

    http.expectNone(URL);
    expect(element('asesor-emision')?.getAttribute('data-state')).toBe('no-permission');
    expect(element('no-permission')?.getAttribute('data-required')).toBe('asesor');
  });
});
