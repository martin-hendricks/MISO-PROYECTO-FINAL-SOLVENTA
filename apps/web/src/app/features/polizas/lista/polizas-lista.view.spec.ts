import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { POLIZAS } from '../polizas.testing';
import { PolizasListaView } from './polizas-lista.view';

describe('PolizasListaView', () => {
  const URL = '/web/cliente/polizas';

  function render() {
    TestBed.configureTestingModule({
      imports: [PolizasListaView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
      ],
    });
    const fixture = TestBed.createComponent(PolizasListaView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('shows the wallet with validity, status and premium in the active locale', () => {
    const { fixture, http, host, element } = render();

    expect(element('polizas-loading')).not.toBeNull();
    http.expectOne(URL).flush({ polizas: POLIZAS });
    fixture.detectChanges();

    expect(host.querySelectorAll('tbody tr').length).toBe(2);
    const vigente = element('poliza-POL-2026-00088421')!;
    expect(vigente.textContent).toContain('Hogar');
    expect(vigente.textContent).toContain('12/03/2026');
    expect(vigente.textContent).toContain('12/03/2027');
    expect(vigente.textContent).toContain('Vigente');
    expect(vigente.textContent).toContain('42.300');
    expect(vigente.textContent).toContain('COP');
    expect(element('poliza-POL-2025-00090102')?.textContent).toContain('Cancelada');
  });

  it('opens the policy detail from its number', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ polizas: POLIZAS });
    fixture.detectChanges();

    const link = element('poliza-POL-2026-00088421')!.querySelector('a');
    expect(link?.getAttribute('href')).toBe('/polizas/POL-2026-00088421');
  });

  it('offers no renew, modify or cancel action', () => {
    const { fixture, http, host } = render();
    http.expectOne(URL).flush({ polizas: POLIZAS });
    fixture.detectChanges();

    expect(host.querySelectorAll('button').length).toBe(0);
    expect(host.textContent).not.toMatch(/Renovar|Modificar|Cancelar/);
  });

  it('shows the empty state when the wallet has no policies', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush({ polizas: [] });
    fixture.detectChanges();

    expect(element('polizas-empty')).not.toBeNull();
    expect(element('polizas-table')).toBeNull();
  });

  it('offers to retry in the same view when the list fails', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    element('polizas-retry')!.click();
    http.expectOne(URL).flush({ polizas: POLIZAS });
    fixture.detectChanges();

    expect(element('polizas-error')).toBeNull();
    expect(element('polizas-table')).not.toBeNull();
  });
});
