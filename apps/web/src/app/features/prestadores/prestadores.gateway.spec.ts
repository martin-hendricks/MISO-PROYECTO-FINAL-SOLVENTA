import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { PrestadoresGateway, ServicioNoDisponible, servicioCaido } from './prestadores.gateway';

describe('PrestadoresGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return {
      gateway: TestBed.inject(PrestadoresGateway),
      http: TestBed.inject(HttpTestingController),
    };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('asks for providers near a position with ramo and radioKm, in camelCase', () => {
    const { gateway, http } = setup();
    let cuerpo: unknown;
    gateway
      .buscar({ lat: 4.6432, lng: -74.0631, ramo: 'soat-motocicleta', radioKm: 10 })
      .subscribe((r) => (cuerpo = r));

    const req = http.expectOne(
      (call) => call.url === '/web/cliente/prestadores' && call.method === 'GET',
    );
    expect(req.request.params.get('lat')).toBe('4.6432');
    expect(req.request.params.get('lng')).toBe('-74.0631');
    expect(req.request.params.get('ramo')).toBe('soat-motocicleta');
    expect(req.request.params.get('radioKm')).toBe('10');
    req.flush({
      centro: { lat: 4.6432, lng: -74.0631, origen: 'posicion' },
      radioKm: 10,
      prestadores: [
        {
          id: 'PRE-BOG-06',
          nombre: 'Taller Moto Chapinero',
          tipo: 'taller-motos',
          ramos: ['soat-motocicleta'],
          direccion: 'Cra 13 #45-18',
          ciudad: 'Bogotá',
          barrio: 'Chapinero',
          lat: '4.6355',
          lng: '-74.0655',
          telefono: '601 555 0112',
          horario: 'Lun–Sáb 7:00–19:00',
          distanciaKm: 0.9,
        },
        {
          id: 'PRE-BOG-07',
          nombre: 'Sin distancia',
          tipo: 'grua',
          direccion: 'Cra 1',
          ciudad: 'Bogotá',
          barrio: 'Chapinero',
          lat: 1,
          lng: 2,
          telefono: '1',
          horario: 'Lun',
          distanciaKm: null,
        },
      ],
    });

    expect(cuerpo).toEqual({
      centro: { lat: 4.6432, lng: -74.0631, origen: 'posicion' },
      radioKm: 10,
      prestadores: [
        jasmine.objectContaining({ id: 'PRE-BOG-06', lat: 4.6355, lng: -74.0655, distanciaKm: 0.9 }),
        jasmine.objectContaining({ id: 'PRE-BOG-07', ramos: [], distanciaKm: null }),
      ],
    });
  });

  it('asks by city and omits ramo when the chip is Todos', () => {
    const { gateway, http } = setup();
    gateway.buscar({ ciudad: 'Bogotá', ramo: null }).subscribe();
    const req = http.expectOne((call) => call.url === '/web/cliente/prestadores');
    expect(req.request.params.get('ciudad')).toBe('Bogotá');
    expect(req.request.params.has('lat')).toBeFalse();
    expect(req.request.params.has('ramo')).toBeFalse();
    expect(req.request.params.has('radioKm')).toBeFalse();
    req.flush({});
  });

  it('maps servicio_no_disponible to an error the view model can retry', () => {
    const { gateway, http } = setup();
    let fallo: unknown;
    gateway.buscar({ ciudad: 'Medellín' }).subscribe({ error: (error) => (fallo = error) });
    http
      .expectOne((call) => call.url === '/web/cliente/prestadores')
      .flush({ detail: 'servicio_no_disponible' }, { status: 503, statusText: 'Unavailable' });
    expect(fallo).toBeInstanceOf(ServicioNoDisponible);
    let otro: unknown;
    servicioCaido('red').subscribe({ error: (error) => (otro = error) });
    expect(otro).toBe('red');
  });

  it('passes other failures through and defaults radioKm when the position omits it', () => {
    const { gateway, http } = setup();
    let fallo = false;
    gateway.buscar({ lat: 1, lng: 2 }).subscribe({ error: () => (fallo = true) });
    const req = http.expectOne((call) => call.url === '/web/cliente/prestadores');
    expect(req.request.params.get('radioKm')).toBe('10');
    req.flush({ detail: 'otro' }, { status: 500, statusText: 'Error' });
    expect(fallo).toBeTrue();
  });

  it('reads providers of a claim and returns null on 404', () => {
    const { gateway, http } = setup();
    let encontrado: unknown = 'pendiente';
    let ajeno: unknown = 'pendiente';
    gateway.porSiniestro('sin-1988').subscribe((r) => (encontrado = r));
    const req = http.expectOne('/web/cliente/siniestros/sin-1988/prestadores?radioKm=10');
    req.flush({
      siniestro: { id: 'sin-1988', numero: 'SIN-1988', ramo: 'soat-motocicleta' },
      ramoFijo: 'soat-motocicleta',
      sinGeoetiqueta: false,
      centro: { lat: 4.626, lng: -74.15, origen: 'siniestro' },
      radioKm: 10,
      prestadores: [],
    });
    expect(encontrado).toEqual(
      jasmine.objectContaining({
        ramoFijo: 'soat-motocicleta',
        sinGeoetiqueta: false,
        prestadores: [],
      }),
    );

    gateway.porSiniestro('ajeno', 12).subscribe((r) => (ajeno = r));
    http
      .expectOne('/web/cliente/siniestros/ajeno/prestadores?radioKm=12')
      .flush({ detail: 'no_encontrado' }, { status: 404, statusText: 'Not Found' });
    expect(ajeno).toBeNull();
  });

  it('maps a claim read of servicio_no_disponible to the same error', () => {
    const { gateway, http } = setup();
    let fallo: unknown;
    gateway.porSiniestro('sin-1').subscribe({ error: (error) => (fallo = error) });
    http
      .expectOne('/web/cliente/siniestros/sin-1/prestadores?radioKm=10')
      .flush({ detail: 'servicio_no_disponible' }, { status: 503, statusText: 'Unavailable' });
    expect(fallo).toBeInstanceOf(ServicioNoDisponible);
  });
});
