import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { esRechazoAviso, SiniestrosGateway } from './siniestros.gateway';
import { HttpErrorResponse } from '@angular/common/http';

describe('SiniestrosGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return {
      gateway: TestBed.inject(SiniestrosGateway),
      http: TestBed.inject(HttpTestingController),
    };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('envía el aviso como multipart con clave de idempotencia y ubicación', () => {
    const { gateway, http } = setup();
    const archivo = new File(['png'], 'dano.png', { type: 'image/png' });
    let recibido: unknown;

    gateway
      .report(
        {
          poliza: 'POL-88421',
          fechaHecho: '2026-11-01',
          descripcion: 'Pantalla rota',
          archivo,
          ubicacion: { lat: 4.65, lng: -74.08, precisionM: 12 },
        },
        'clave-1',
      )
      .subscribe((r) => (recibido = r));

    const req = http.expectOne('/web/cliente/siniestros');
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('Idempotency-Key')).toBe('clave-1');
    const form = req.request.body as FormData;
    expect(form.get('poliza')).toBe('POL-88421');
    expect(form.get('fechaHecho')).toBe('2026-11-01');
    expect((form.get('archivos') as File).name).toBe('dano.png');
    expect(JSON.parse(form.get('geo') as string)).toEqual({
      lat: 4.65,
      lng: -74.08,
      precisionM: 12,
    });
    req.flush({ id: 'x', siniestroId: 'SIN-1001', estado: 'recibido' });
    expect(recibido).toEqual({ id: 'x', siniestroId: 'SIN-1001', estado: 'recibido' });
  });

  it('omite la ubicación cuando el usuario la negó', () => {
    const { gateway, http } = setup();
    gateway
      .report(
        {
          poliza: 'POL-1',
          fechaHecho: '2026-11-01',
          descripcion: 'x',
          archivo: new File(['a'], 'a.pdf', { type: 'application/pdf' }),
          ubicacion: null,
        },
        'k',
      )
      .subscribe();
    const req = http.expectOne('/web/cliente/siniestros');
    expect((req.request.body as FormData).has('geo')).toBeFalse();
    req.flush({});
  });

  it('convierte la reserva a número y devuelve null en 404', () => {
    const { gateway, http } = setup();
    let lista: unknown;
    let detalle: unknown = 'sin-respuesta';
    gateway.list().subscribe((l) => (lista = l));
    http
      .expectOne('/web/cliente/siniestros')
      .flush({ siniestros: [{ id: '1', reserva: '420000.00' }] });
    expect((lista as { reserva: number }[])[0].reserva).toBe(420000);

    gateway.detail('nope').subscribe((d) => (detalle = d));
    http
      .expectOne('/web/cliente/siniestros/nope')
      .flush({}, { status: 404, statusText: 'Not Found' });
    expect(detalle).toBeNull();
  });

  it('propaga los errores distintos de 404 en el detalle', () => {
    const { gateway, http } = setup();
    let fallo = false;
    gateway.detail('x').subscribe({ error: () => (fallo = true) });
    http
      .expectOne('/web/cliente/siniestros/x')
      .flush({}, { status: 503, statusText: 'Unavailable' });
    expect(fallo).toBeTrue();
  });

  it('reconoce el rechazo tipificado del núcleo', () => {
    setup();
    const error = new HttpErrorResponse({
      status: 422,
      error: {
        codigo: 'evidencia_tipo_no_permitido',
        mensaje: 'La evidencia debe ser PNG, JPG, PDF o MP4',
      },
    });
    expect(esRechazoAviso(error)?.codigo).toBe('evidencia_tipo_no_permitido');
    expect(esRechazoAviso(new HttpErrorResponse({ status: 503 }))).toBeNull();
    // 409 sin cuerpo: se usan valores por defecto.
    expect(esRechazoAviso(new HttpErrorResponse({ status: 409, error: null }))).toEqual({
      codigo: 'rechazado',
      mensaje: '',
    });
  });
});
