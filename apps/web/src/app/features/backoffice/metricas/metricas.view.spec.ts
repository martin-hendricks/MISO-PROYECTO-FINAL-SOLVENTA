import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { MetricasView } from './metricas.view';

const WIRE = {
  conteos: [
    { tipo: 'PolizaEmitida', fecha: '2026-10-01', cantidad: 3 },
    { tipo: 'PolizaCancelada', fecha: '2026-10-02', cantidad: 1 },
  ],
};

describe('MetricasView', () => {
  const METRICAS_URL = '/web/operador/metricas';

  function render(role: Role = 'operador') {
    TestBed.configureTestingModule({
      imports: [MetricasView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
      ],
    });
    const fixture = TestBed.createComponent(MetricasView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) => host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('blocks a non-operador role without requesting anything', () => {
    const { element } = render('asesor');

    expect(element('metricas')?.getAttribute('data-state')).toBe('no-permission');
  });

  it('lists the aggregated counts for the operador role', () => {
    const { fixture, http, element } = render();

    http.expectOne((req) => req.url === METRICAS_URL).flush(WIRE);
    fixture.detectChanges();

    expect(element('metricas-table')).not.toBeNull();
    expect(element('conteo-PolizaEmitida-2026-10-01')).not.toBeNull();
    expect(element('conteo-PolizaCancelada-2026-10-02')).not.toBeNull();
  });

  it('shows an empty state when there are no events in the range', () => {
    const { fixture, http, element } = render();

    http.expectOne((req) => req.url === METRICAS_URL).flush({ conteos: [] });
    fixture.detectChanges();

    expect(element('metricas-empty')).not.toBeNull();
  });

  it('shows a retryable error state when the request fails', () => {
    const { fixture, http, element } = render();

    http.expectOne((req) => req.url === METRICAS_URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    expect(element('metricas-error')).not.toBeNull();
  });

  it('retries the request when the retry button is clicked', () => {
    const { fixture, http, element } = render();

    http.expectOne((req) => req.url === METRICAS_URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    element('metricas-retry')!.click();
    http.expectOne((req) => req.url === METRICAS_URL).flush(WIRE);
    fixture.detectChanges();

    expect(element('metricas-table')).not.toBeNull();
  });
});
