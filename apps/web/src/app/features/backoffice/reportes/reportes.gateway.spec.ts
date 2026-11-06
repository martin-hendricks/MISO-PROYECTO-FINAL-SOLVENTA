import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ReporteGenerado, ReportesGateway } from './reportes.gateway';

const WIRE = {
  nombre_archivo: 'regulador_2026-10-01_2026-10-31.csv',
  tipo_contenido: 'text/csv',
  contenido: 'numero,estado\nPOL-1,vigente\n',
};

const REPORTE: ReporteGenerado = {
  nombreArchivo: 'regulador_2026-10-01_2026-10-31.csv',
  tipoContenido: 'text/csv',
  contenido: 'numero,estado\nPOL-1,vigente\n',
};

describe('ReportesGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return {
      gateway: TestBed.inject(ReportesGateway),
      http: TestBed.inject(HttpTestingController),
    };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('requests the regulator report with the date range', () => {
    const { gateway, http } = setup();
    let resultado: ReporteGenerado | undefined;

    gateway.regulador('2026-10-01', '2026-10-31').subscribe((reporte) => (resultado = reporte));
    const request = http.expectOne(
      (req) => req.url === '/web/operador/reportes/regulador',
    );
    expect(request.request.params.get('desde')).toBe('2026-10-01');
    expect(request.request.params.get('hasta')).toBe('2026-10-31');
    request.flush(WIRE);

    expect(resultado).toEqual(REPORTE);
  });

  it('requests the reinsurer extract with the date range', () => {
    const { gateway, http } = setup();
    let resultado: ReporteGenerado | undefined;

    gateway
      .reaseguradora('2026-10-01', '2026-10-31')
      .subscribe((reporte) => (resultado = reporte));
    const request = http.expectOne(
      (req) => req.url === '/web/operador/reportes/reaseguradora',
    );
    request.flush({ ...WIRE, nombre_archivo: 'reaseguradora_2026-10-01_2026-10-31.csv' });

    expect(resultado?.nombreArchivo).toBe('reaseguradora_2026-10-01_2026-10-31.csv');
  });
});
