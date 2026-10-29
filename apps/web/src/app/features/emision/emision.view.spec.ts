import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { EMITIDA, MOTIVO, RECHAZADA } from './emision.testing';
import { EmisionView } from './emision.view';

describe('EmisionView', () => {
  const URL = '/web/cliente/polizas';
  const OFERTA = { cotizacion: 'COT-0042' };

  function render(query: Record<string, string> = OFERTA) {
    TestBed.configureTestingModule({
      imports: [EmisionView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: convertToParamMap(query) } },
        },
      ],
    });
    const navigate = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(EmisionView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element, navigate };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('accepts the offer and shows the progress while the core issues', () => {
    const { http, element } = render();

    const request = http.expectOne(URL);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ cotizacionId: 'COT-0042' });
    expect(element('emision-progreso')).not.toBeNull();
    expect(element('emision-progreso')?.querySelector('[role="progressbar"]')).not.toBeNull();
    request.flush(EMITIDA);
  });

  it('shows the issued policy with number, validity and premium', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush(EMITIDA);
    fixture.detectChanges();

    expect(element('emision-progreso')).toBeNull();
    const emitida = element('poliza-emitida')!;
    expect(emitida.textContent).toContain('POL-2026-00088421');
    expect(emitida.textContent).toContain('12/03/2026');
    expect(emitida.textContent).toContain('12/03/2027');
    expect(emitida.textContent).toContain('42.300');
  });

  it('opens the policy detail or Inicio from the issued policy', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(EMITIDA);
    fixture.detectChanges();

    expect(element('ver-poliza')?.getAttribute('href')).toBe('/polizas/POL-2026-00088421');
    expect(element('ir-inicio')?.getAttribute('href')).toBe('/');
  });

  it('goes to the rejected subscription with the stored reason when the core rejects', () => {
    const { fixture, http, element, navigate } = render();

    http.expectOne(URL).flush(RECHAZADA);
    fixture.detectChanges();

    expect(navigate).toHaveBeenCalledWith(['/suscripcion-rechazada'], {
      state: { motivo: MOTIVO },
    });
    expect(element('poliza-emitida')).toBeNull();
  });

  it('offers to retry in the same view when the request fails', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    element('emision-retry')!.click();
    http.expectOne(URL).flush(EMITIDA);
    fixture.detectChanges();

    expect(element('emision-error')).toBeNull();
    expect(element('poliza-emitida')).not.toBeNull();
  });

  it('keeps the portal top bar without destinations while the core issues', () => {
    const { http, host, element } = render();

    expect(element('portal-title')).not.toBeNull();
    expect(host.querySelector('nav')).toBeNull();
    expect(element('sign-out')).toBeNull();
    http.expectOne(URL).flush(EMITIDA);
  });

  it('does not call the BFF without an offer to accept', () => {
    const { http, element } = render({});

    http.expectNone(URL);
    expect(element('emision-invalid')).not.toBeNull();
    expect(element('emision-invalid')?.querySelector('a')?.getAttribute('href')).toBe('/');
  });
});
