import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { AVISOS } from '../polizas.testing';
import { PolizasAvisosView } from './polizas-avisos.view';

describe('PolizasAvisosView', () => {
  const URL = '/web/cliente/polizas/por-vencer';

  function render() {
    TestBed.configureTestingModule({
      imports: [PolizasAvisosView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
      ],
    });
    const fixture = TestBed.createComponent(PolizasAvisosView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('shows the expiry notice for a policy about to expire', () => {
    const { fixture, http, host, element } = render();

    expect(element('avisos-loading')).not.toBeNull();
    http.expectOne(URL).flush({ polizas: AVISOS });
    fixture.detectChanges();

    const aviso = element('aviso-POL-2026-00088421')!;
    expect(aviso.textContent).toContain('Hogar');
    expect(aviso.textContent).toContain('12/03/2027');
    expect(host.querySelector('[data-testid="avisos-list"] a')?.getAttribute('href')).toBe(
      '/polizas/POL-2026-00088421',
    );
  });

  it('cannot renew it from the notice -- no renew action is offered', () => {
    const { fixture, http, host } = render();
    http.expectOne(URL).flush({ polizas: AVISOS });
    fixture.detectChanges();

    expect(host.querySelectorAll('button').length).toBe(0);
    expect(host.textContent).not.toMatch(/Renovar/);
  });

  it('shows the empty state when there is no policy about to expire', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush({ polizas: [] });
    fixture.detectChanges();

    expect(element('avisos-empty')).not.toBeNull();
    expect(element('avisos-list')).toBeNull();
  });

  it('offers to retry in the same view when the notice list fails', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    element('avisos-retry')!.click();
    http.expectOne(URL).flush({ polizas: AVISOS });
    fixture.detectChanges();

    expect(element('avisos-error')).toBeNull();
    expect(element('avisos-list')).not.toBeNull();
  });
});
