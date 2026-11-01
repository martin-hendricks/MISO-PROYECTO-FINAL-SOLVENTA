import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { pagina, VENCIDA, VIGENTE } from './cotizaciones.testing';
import { CotizacionesView } from './cotizaciones.view';

describe('CotizacionesView', () => {
  const URL = '/web/asesor/cotizaciones';
  const query = (incluirVencidas: boolean, page = 1) =>
    `${URL}?incluirVencidas=${incluirVencidas}&pagina=${page}&tamano=20`;

  function render(role: Role) {
    TestBed.configureTestingModule({
      imports: [CotizacionesView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
      ],
    });
    const fixture = TestBed.createComponent(CotizacionesView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('lists each pending quote with client, line, premium, status and dates (S4)', () => {
    const { fixture, http, element } = render('asesor');

    expect(element('cotizaciones-loading')).not.toBeNull();
    http.expectOne(query(false)).flush(pagina([VIGENTE]));
    fixture.detectChanges();

    const row = element('cotizacion-COT-1')!;
    expect(row.textContent).toContain('CLI-18');
    expect(row.textContent).toContain('autos');
    expect(row.textContent).toContain('42.300');
    expect(row.textContent).toContain('COP');
    expect(row.textContent).toContain('Cotizada');
    expect(row.textContent).toContain('20/10/2026');
    expect(row.textContent).toContain('19/11/2026');
  });

  it('continues the issuance of a quote without quoting again (S5)', () => {
    const { fixture, http, element } = render('asesor');
    http.expectOne(query(false)).flush(pagina([VIGENTE]));
    fixture.detectChanges();

    expect(element('continuar-COT-1')?.getAttribute('href')).toBe(
      '/cms/cotizaciones/COT-1/emision',
    );
  });

  it('shows the expired quotes marked and without the action when toggled (S3)', () => {
    const { fixture, http, element } = render('asesor');
    http.expectOne(query(false)).flush(pagina([VIGENTE]));
    fixture.detectChanges();

    element('cotizaciones-vencidas')!.click();
    http.expectOne(query(true)).flush(pagina([VIGENTE, VENCIDA]));
    fixture.detectChanges();

    expect(element('cotizacion-COT-2')?.getAttribute('data-vencida')).toBe('true');
    expect(element('cotizacion-COT-2')?.textContent).toContain('Vencida');
    expect(element('continuar-COT-2')).toBeNull();
    expect(element('continuar-COT-1')).not.toBeNull();
  });

  it('shows the empty state with a new quote call to action (S6)', () => {
    const { fixture, http, element } = render('asesor');
    http.expectOne(query(false)).flush(pagina([]));
    fixture.detectChanges();

    expect(element('cotizaciones-table')).toBeNull();
    expect(element('cotizaciones-empty-cta')?.getAttribute('href')).toBe('/cms/cotizaciones/nueva');
  });

  it('pages forward and back using hayMas (S8)', () => {
    const { fixture, http, element } = render('asesor');
    http.expectOne(query(false)).flush(pagina([VIGENTE], { hayMas: true }));
    fixture.detectChanges();

    expect((element('cotizaciones-prev') as HTMLButtonElement).disabled).toBeTrue();
    element('cotizaciones-next')!.click();
    http.expectOne(query(false, 2)).flush(pagina([VENCIDA], { pagina: 2, hayMas: false }));
    fixture.detectChanges();

    expect((element('cotizaciones-next') as HTMLButtonElement).disabled).toBeTrue();
    element('cotizaciones-prev')!.click();
    http.expectOne(query(false, 1)).flush(pagina([VIGENTE], { hayMas: true }));
  });

  it('warns when the accepted quotes could not be verified (S10)', () => {
    const { fixture, http, element } = render('asesor');
    http.expectOne(query(false)).flush(pagina([VIGENTE], { avisos: ['polizas_no_disponible'] }));
    fixture.detectChanges();

    expect(element('cotizaciones-aviso')?.textContent).toContain(
      'No se pudo verificar el estado de algunas cotizaciones aceptadas',
    );
  });

  it('shows no warning when every quote was verified (S10)', () => {
    const { fixture, http, element } = render('asesor');
    http.expectOne(query(false)).flush(pagina([VIGENTE]));
    fixture.detectChanges();

    expect(element('cotizaciones-aviso')).toBeNull();
  });

  it('offers to retry in the same view when the list fails', () => {
    const { fixture, http, element } = render('asesor');
    http.expectOne(query(false)).error(new ProgressEvent('error'));
    fixture.detectChanges();

    element('cotizaciones-retry')!.click();
    http.expectOne(query(false)).flush(pagina([VIGENTE]));
    fixture.detectChanges();

    expect(element('cotizaciones-error')).toBeNull();
    expect(element('cotizaciones-table')).not.toBeNull();
  });

  it('keeps the list from the operator without calling the BFF (S7)', () => {
    const { http, element } = render('operador');

    http.expectNone((req) => req.url.startsWith(URL));
    expect(element('section-cotizaciones')?.getAttribute('data-state')).toBe('no-permission');
    expect(element('no-permission')?.getAttribute('data-required')).toBe('asesor');
  });
});
