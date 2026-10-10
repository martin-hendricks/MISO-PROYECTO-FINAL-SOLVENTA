import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { CLIENTES } from './clientes.testing';
import { ClientesView } from './clientes.view';

describe('ClientesView', () => {
  const URL = '/web/asesor/clientes';

  function render(role: Role) {
    TestBed.configureTestingModule({
      imports: [ClientesView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
      ],
    });
    const fixture = TestBed.createComponent(ClientesView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('shows the client KPIs and the read-only list for the advisor', () => {
    const { fixture, http, host, element } = render('asesor');

    expect(element('clientes-loading')).not.toBeNull();
    http.expectOne(URL).flush({ clientes: CLIENTES });
    fixture.detectChanges();

    expect(element('kpi-active')?.querySelector('.kpi-value')?.textContent).toBe('4');
    expect(element('kpi-web')?.querySelector('.kpi-value')?.textContent).toBe('3');
    expect(element('kpi-android')?.querySelector('.kpi-value')?.textContent).toBe('2');
    expect(element('kpi-pendingConsent')?.querySelector('.kpi-value')?.textContent).toBe('1');
    expect(host.querySelectorAll('tbody tr').length).toBe(5);
    expect(element('cliente-CLI-22')?.textContent).toContain('Inactivo');
    expect(element('cliente-CLI-22')?.textContent).toContain('Revocado');
    expect((element('clientes-new') as HTMLButtonElement).disabled).toBeTrue();
  });

  it('shows the empty state when the portfolio has no clients', () => {
    const { fixture, http, element } = render('asesor');

    http.expectOne(URL).flush({ clientes: [] });
    fixture.detectChanges();

    expect(element('clientes-empty')).not.toBeNull();
    expect(element('clientes-table')).toBeNull();
  });

  it('offers to retry in the same view when the list fails', () => {
    const { fixture, http, element } = render('asesor');
    http.expectOne(URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    element('clientes-retry')!.click();
    http.expectOne(URL).flush({ clientes: CLIENTES });
    fixture.detectChanges();

    expect(element('clientes-error')).toBeNull();
    expect(element('clientes-table')).not.toBeNull();
  });

  it('keeps the list from the operator without calling the BFF', () => {
    const { http, element } = render('operador');

    http.expectNone(URL);
    expect(element('section-clientes')?.getAttribute('data-state')).toBe('no-permission');
    expect(element('no-permission')?.getAttribute('data-required')).toBe('asesor');
    expect(element('clientes-new')).toBeNull();
  });
});
