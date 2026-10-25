import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { DETALLE } from '../polizas.testing';
import { PolizaDetalleView } from './poliza-detalle.view';

describe('PolizaDetalleView', () => {
  const NUMERO = 'POL-2026-00088421';
  const URL = `/web/cliente/polizas/${NUMERO}`;

  function render() {
    TestBed.configureTestingModule({
      imports: [PolizaDetalleView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ numero: NUMERO }) } },
        },
      ],
    });
    const fixture = TestBed.createComponent(PolizaDetalleView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('shows number, product, coverages with limits, validity, status and premium', () => {
    const { fixture, http, element } = render();

    expect(element('poliza-loading')).not.toBeNull();
    http.expectOne(URL).flush(DETALLE);
    fixture.detectChanges();

    expect(element('poliza-title')?.textContent).toContain('Hogar');
    expect(element('poliza-title')?.textContent).toContain(NUMERO);
    expect(element('poliza-estado')?.textContent?.trim()).toBe('Vigente');
    expect(element('poliza-vigencia')?.textContent).toContain('12/03/2026');
    expect(element('poliza-vigencia')?.textContent).toContain('12/03/2027');
    const coberturas = element('poliza-coberturas')!.querySelectorAll('li');
    expect(coberturas.length).toBe(3);
    expect(coberturas[0].textContent).toContain('Incendio y terremoto');
    expect(coberturas[0].textContent).toContain('400.000.000');
    expect(element('poliza-prima')?.textContent).toContain('42.300');
    expect(element('poliza-prima')?.textContent).toContain('COP');
  });

  it('is read-only: no renew, modify or cancel action', () => {
    const { fixture, http, host } = render();
    http.expectOne(URL).flush(DETALLE);
    fixture.detectChanges();

    expect(host.querySelectorAll('button').length).toBe(0);
    expect(host.textContent).not.toMatch(/Renovar|Modificar|Cancelar/);
  });

  it('shows the real core status when the operator cancelled the policy', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ ...DETALLE, estado: 'CANCELADA' });
    fixture.detectChanges();

    expect(element('poliza-estado')?.textContent?.trim()).toBe('Cancelada');
  });

  it('goes back to the policy list', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(DETALLE);
    fixture.detectChanges();

    expect(element('poliza-back')?.getAttribute('href')).toBe('/polizas');
  });

  it('shows a neutral not-found state with a way back to the list', () => {
    const { fixture, http, element, host } = render();

    http
      .expectOne(URL)
      .flush({ codigo: 'POLIZA_NO_ENCONTRADA' }, { status: 404, statusText: 'Not Found' });
    fixture.detectChanges();

    expect(element('poliza-not-found')).not.toBeNull();
    expect(element('poliza-not-found')?.querySelector('a')?.getAttribute('href')).toBe('/polizas');
    expect(host.textContent).not.toContain(NUMERO);
    expect(element('poliza-coberturas')).toBeNull();
  });

  it('offers to retry in the same view when the detail fails', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    element('poliza-retry')!.click();
    http.expectOne(URL).flush(DETALLE);
    fixture.detectChanges();

    expect(element('poliza-error')).toBeNull();
    expect(element('poliza-coberturas')).not.toBeNull();
  });
});
