import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Conteo, MetricasGateway } from './metricas.gateway';

const WIRE = {
  conteos: [
    { tipo: 'PolizaEmitida', fecha: '2026-10-01', cantidad: 3 },
    { tipo: 'PolizaCancelada', fecha: '2026-10-02', cantidad: 1 },
  ],
};

describe('MetricasGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return {
      gateway: TestBed.inject(MetricasGateway),
      http: TestBed.inject(HttpTestingController),
    };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('requests the aggregated counts with the date range', () => {
    const { gateway, http } = setup();
    let resultado: Conteo[] | undefined;

    gateway.conteos('2026-10-01', '2026-10-31').subscribe((conteos) => (resultado = conteos));
    const request = http.expectOne((req) => req.url === '/web/operador/metricas');
    expect(request.request.params.get('desde')).toBe('2026-10-01');
    expect(request.request.params.get('hasta')).toBe('2026-10-31');
    request.flush(WIRE);

    expect(resultado).toEqual(WIRE.conteos as Conteo[]);
  });
});
