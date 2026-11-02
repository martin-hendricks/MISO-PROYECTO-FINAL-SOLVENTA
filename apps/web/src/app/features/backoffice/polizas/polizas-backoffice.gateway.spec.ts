import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { PolizaOperador, PolizasBackofficeGateway, rechazoDePoliza } from './polizas-backoffice.gateway';

const WIRE = {
  numero: 'POL-2026-00000001',
  ramo: 'Protección de dispositivo',
  estado: 'vigente' as const,
  venceEn: '2027-10-01',
  prima: { valor: '1000.00', periodicidad: 'ANUAL' },
  renovable: true,
  devolucionEstimada: null,
  canceladaEn: null,
  canceladaPor: null,
  motivoCancelacion: null,
  siniestrosAbiertos: null,
};

const POLIZA: PolizaOperador = {
  ...WIRE,
  prima: { valor: 1000, periodicidad: 'ANUAL' },
};

describe('PolizasBackofficeGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return {
      gateway: TestBed.inject(PolizasBackofficeGateway),
      http: TestBed.inject(HttpTestingController),
    };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('finds a policy by its number and numeric amounts the core sends as strings', () => {
    const { gateway, http } = setup();
    let resultado: PolizaOperador | null | undefined;

    gateway.buscarPorNumero('POL-2026-00000001').subscribe((poliza) => (resultado = poliza));
    const request = http.expectOne('/web/operador/polizas/POL-2026-00000001');
    expect(request.request.method).toBe('GET');
    request.flush(WIRE);

    expect(resultado).toEqual(POLIZA);
  });

  it('maps a missing policy (404) to null', () => {
    const { gateway, http } = setup();
    let resultado: PolizaOperador | null | undefined;

    gateway.buscarPorNumero('POL-NO-EXISTE').subscribe((poliza) => (resultado = poliza));
    http.expectOne('/web/operador/polizas/POL-NO-EXISTE').flush(null, { status: 404, statusText: 'Not Found' });

    expect(resultado).toBeNull();
  });

  it('lets any other lookup failure through', () => {
    const { gateway, http } = setup();
    let failure: unknown;

    gateway.buscarPorNumero('POL-1').subscribe({ error: (error: unknown) => (failure = error) });
    http.expectOne('/web/operador/polizas/POL-1').flush({}, { status: 503, statusText: 'Unavailable' });

    expect((failure as HttpErrorResponse).status).toBe(503);
  });

  it('renews by number through the ciclo endpoint', () => {
    const { gateway, http } = setup();
    let resultado: PolizaOperador | undefined;

    gateway.renovar('POL-2026-00000001').subscribe((poliza) => (resultado = poliza));
    const request = http.expectOne('/web/operador/polizas/ciclo');
    expect(request.request.body).toEqual({ numero: 'POL-2026-00000001', verbo: 'renovar' });
    request.flush(WIRE);

    expect(resultado).toEqual(POLIZA);
  });

  it('cancels by number and reason through the ciclo endpoint', () => {
    const { gateway, http } = setup();
    let resultado: PolizaOperador | undefined;

    gateway.cancelar('POL-2026-00000001', 'El cliente lo pidió').subscribe((poliza) => (resultado = poliza));
    const request = http.expectOne('/web/operador/polizas/ciclo');
    expect(request.request.body).toEqual({
      numero: 'POL-2026-00000001',
      verbo: 'cancelar',
      motivo: 'El cliente lo pidió',
    });
    request.flush({ ...WIRE, estado: 'cancelada' });

    expect(resultado?.estado).toBe('cancelada');
  });

  it('reads 409 and 422 as typed business rejections only', () => {
    setup();
    expect(
      rechazoDePoliza(
        new HttpErrorResponse({ status: 409, error: { codigo: 'ya_cancelada', mensaje: 'Ya cancelada' } }),
      ),
    ).toEqual({ codigo: 'ya_cancelada', mensaje: 'Ya cancelada' });
    expect(rechazoDePoliza(new HttpErrorResponse({ status: 422, error: {} }))).toEqual({
      codigo: 'rechazo',
      mensaje: '',
    });
    expect(rechazoDePoliza(new HttpErrorResponse({ status: 500 }))).toBeNull();
    expect(rechazoDePoliza(new Error('boom'))).toBeNull();
  });
});
