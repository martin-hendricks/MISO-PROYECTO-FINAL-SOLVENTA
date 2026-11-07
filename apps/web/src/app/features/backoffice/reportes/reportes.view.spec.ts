import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { ReportesView } from './reportes.view';

const WIRE = {
  nombre_archivo: 'regulador_2026-10-01_2026-11-06.csv',
  tipo_contenido: 'text/csv',
  contenido: 'numero,estado\nPOL-1,vigente\n',
};

describe('ReportesView', () => {
  const REGULADOR_URL = '/web/operador/reportes/regulador';
  const REASEGURADORA_URL = '/web/operador/reportes/reaseguradora';

  function render(role: Role = 'operador') {
    TestBed.configureTestingModule({
      imports: [ReportesView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
      ],
    });
    const fixture = TestBed.createComponent(ReportesView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) => host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('blocks a non-operador role', () => {
    const { element } = render('asesor');

    expect(element('reportes')?.getAttribute('data-state')).toBe('no-permission');
  });

  it('shows both report cards for the operador role', () => {
    const { element } = render();

    expect(element('reporte-regulador')).not.toBeNull();
    expect(element('reporte-reaseguradora')).not.toBeNull();
  });

  it('requests the regulator report when generar is clicked', () => {
    const { fixture, http, element } = render();

    element('reporte-regulador-generar')!.click();

    const request = http.expectOne((req) => req.url === REGULADOR_URL);
    request.flush(WIRE);
    fixture.detectChanges();

    expect(element('reporte-regulador-descargar')).not.toBeNull();
  });

  it('requests the reinsurer extract independently from the regulator report', () => {
    const { fixture, http, element } = render();

    element('reporte-reaseguradora-generar')!.click();

    const request = http.expectOne((req) => req.url === REASEGURADORA_URL);
    request.flush({ ...WIRE, nombre_archivo: 'reaseguradora.csv' });
    fixture.detectChanges();

    expect(element('reporte-reaseguradora-descargar')).not.toBeNull();
    expect(element('reporte-regulador-descargar')).toBeNull();
  });

  it('shows a retryable error state when the regulator report fails', () => {
    const { fixture, http, element } = render();

    element('reporte-regulador-generar')!.click();
    http.expectOne((req) => req.url === REGULADOR_URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    expect(element('reporte-regulador-error')).not.toBeNull();
    expect(element('reporte-regulador-descargar')).toBeNull();
  });

  it('downloads the generated report as a file', () => {
    const { fixture, http, element } = render();
    const createObjectURL = spyOn(URL, 'createObjectURL').and.returnValue('blob:fake');
    const revokeObjectURL = spyOn(URL, 'revokeObjectURL');

    element('reporte-regulador-generar')!.click();
    http.expectOne((req) => req.url === REGULADOR_URL).flush(WIRE);
    fixture.detectChanges();
    element('reporte-regulador-descargar')!.click();

    expect(createObjectURL).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:fake');
  });

  it('downloads the reinsurer extract as a file too', () => {
    const { fixture, http, element } = render();
    spyOn(URL, 'createObjectURL').and.returnValue('blob:fake');
    const revokeObjectURL = spyOn(URL, 'revokeObjectURL');

    element('reporte-reaseguradora-generar')!.click();
    http.expectOne((req) => req.url === REASEGURADORA_URL).flush(WIRE);
    fixture.detectChanges();
    element('reporte-reaseguradora-descargar')!.click();

    expect(revokeObjectURL).toHaveBeenCalledWith('blob:fake');
  });

  it('shows a retryable error state when the reinsurer extract fails', () => {
    const { fixture, http, element } = render();

    element('reporte-reaseguradora-generar')!.click();
    http.expectOne((req) => req.url === REASEGURADORA_URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    expect(element('reporte-reaseguradora-error')).not.toBeNull();
    expect(element('reporte-reaseguradora-descargar')).toBeNull();
  });
});
