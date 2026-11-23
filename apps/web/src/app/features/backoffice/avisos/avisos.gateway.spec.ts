import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AvisosGateway, rechazoDelNucleo } from './avisos.gateway';

describe('AvisosGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return { gateway: TestBed.inject(AvisosGateway), http: TestBed.inject(HttpTestingController) };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('usa las rutas del operador en bff-web', () => {
    const { gateway, http } = setup();
    gateway.cola('aprobados').subscribe();
    http.expectOne('/web/operador/avisos?filtro=aprobados').flush({});
    gateway.caso('a b').subscribe();
    http.expectOne('/web/operador/avisos/a%20b').flush({});
    gateway.decidir('id', 'aprobar', null).subscribe();
    expect(http.expectOne('/web/operador/avisos/decision').request.body).toEqual({
      siniestroId: 'id',
      decision: 'aprobar',
      motivo: null,
    });
    gateway.enrutarAPerito('id', 'Inspección').subscribe();
    expect(http.expectOne('/web/operador/avisos/id/perito').request.body).toEqual({
      motivo: 'Inspección',
    });
    gateway.pagar('id').subscribe();
    expect(http.expectOne('/web/operador/avisos/id/pago').request.method).toBe('POST');
  });

  it('extrae el mensaje del rechazo del núcleo', () => {
    setup();
    expect(
      rechazoDelNucleo(
        new HttpErrorResponse({ status: 422, error: { mensaje: 'Monto sobre umbral' } }),
      ),
    ).toBe('Monto sobre umbral');
    expect(rechazoDelNucleo(new HttpErrorResponse({ status: 409, error: null }))).toBe('');
    expect(rechazoDelNucleo(new HttpErrorResponse({ status: 503 }))).toBeNull();
  });
});
