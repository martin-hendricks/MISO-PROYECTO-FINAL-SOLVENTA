import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Catalogo, CotizacionGateway, Oferta, rechazoDe } from './cotizacion.gateway';
import {
  CATALOGO,
  CATALOGO_WIRE,
  FUERA_DE_RANGO,
  OFERTA,
  OFERTA_DESGLOSE_WIRE,
  OFERTA_WIRE,
} from './cotizacion.testing';

describe('CotizacionGateway', () => {
  const DATOS = { cilindraje_cc: 150, modelo_anio: 2022, ciudad_circulacion: 'bogota' };

  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return {
      gateway: TestBed.inject(CotizacionGateway),
      http: TestBed.inject(HttpTestingController),
    };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('reads the catalog ranges of the line of business for each channel', () => {
    const { gateway, http } = setup();
    const catalogos: Catalogo[] = [];

    gateway.catalog('cliente').subscribe((catalogo) => catalogos.push(catalogo));
    http.expectOne('/web/cliente/catalogo/SOAT%20motocicleta').flush(CATALOGO_WIRE);
    gateway.catalog('asesor').subscribe((catalogo) => catalogos.push(catalogo));
    http.expectOne('/web/asesor/catalogo/SOAT%20motocicleta').flush(CATALOGO_WIRE);

    expect(catalogos).toEqual([CATALOGO, CATALOGO]);
  });

  it('quotes the single line of business for the customer', () => {
    const { gateway, http } = setup();
    let oferta: Oferta | undefined;

    gateway.quote(DATOS).subscribe((answer) => (oferta = answer));

    const request = http.expectOne('/web/cliente/cotizaciones');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ ramo: 'SOAT motocicleta', datosRiesgo: DATOS });
    request.flush(OFERTA_WIRE);
    expect(oferta).toEqual(OFERTA);
  });

  it('quotes on behalf of the customer the advisor serves', () => {
    const { gateway, http } = setup();
    let oferta: Oferta | undefined;

    gateway.quoteFor('CLI-18', DATOS).subscribe((answer) => (oferta = answer));

    const request = http.expectOne('/web/asesor/cotizaciones');
    expect(request.request.body).toEqual({
      clienteId: 'CLI-18',
      ramo: 'SOAT motocicleta',
      datosRiesgo: DATOS,
    });
    request.flush(OFERTA_DESGLOSE_WIRE);
    expect(oferta?.primaNeta).toBe(120000);
    expect(oferta?.expedicion).toBe(8500);
  });

  it('reconsults by id and maps a missing quote to null', () => {
    const { gateway, http } = setup();
    const answers: (Oferta | null)[] = [];

    gateway.find('COT 1').subscribe((answer) => answers.push(answer));
    const request = http.expectOne('/web/cliente/cotizaciones/COT%201');
    expect(request.request.method).toBe('GET');
    request.flush({ ...OFERTA_WIRE, primaNeta: null });
    gateway.find('COT-404').subscribe((answer) => answers.push(answer));
    http
      .expectOne('/web/cliente/cotizaciones/COT-404')
      .flush({}, { status: 404, statusText: 'Not Found' });

    expect(answers).toEqual([OFERTA, null]);
  });

  it('lets any other reconsult failure through', () => {
    const { gateway, http } = setup();
    let failure: unknown;

    gateway.find('COT-1').subscribe({ error: (error: unknown) => (failure = error) });
    http
      .expectOne('/web/cliente/cotizaciones/COT-1')
      .flush({}, { status: 503, statusText: 'Unavailable' });

    expect((failure as HttpErrorResponse).status).toBe(503);
  });

  it('reads 409 and 422 as typed business rejections only', () => {
    setup();
    expect(rechazoDe(new HttpErrorResponse({ status: 422, error: FUERA_DE_RANGO }))).toEqual(
      FUERA_DE_RANGO,
    );
    expect(rechazoDe(new HttpErrorResponse({ status: 409, error: {} }))).toEqual({
      codigo: 'rechazo',
      mensaje: '',
    });
    expect(rechazoDe(new HttpErrorResponse({ status: 500 }))).toBeNull();
    expect(rechazoDe(new Error('boom'))).toBeNull();
  });
});
