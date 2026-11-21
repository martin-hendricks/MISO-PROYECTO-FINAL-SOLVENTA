import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { PrestadoresGateway, ServicioNoDisponible, servicioCaido } from './prestadores.gateway';

const CHAPINERO = { norte: 4.66, sur: 4.62, este: -74.05, oeste: -74.08 };

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
      .buscar({ origen: { lat: 4.6432, lng: -74.0631 }, ramo: 'soat-motocicleta', radioKm: 10 })
      .subscribe((r) => (cuerpo = r));

    const req = http.expectOne(
      (call) => call.url === '/web/cliente/prestadores' && call.method === 'GET',
    );
    expect(req.request.params.get('lat')).toBe('4.6432');
    expect(req.request.params.get('lng')).toBe('-74.0631');
    expect(req.request.params.get('ramo')).toBe('soat-motocicleta');
    expect(req.request.params.get('radioKm')).toBe('10');
    expect(req.request.params.has('norte')).toBeFalse();
    req.flush({
      centro: { lat: 4.6432, lng: -74.0631, origen: 'posicion' },
      radioKm: 10,
      truncado: false,
      prestadores: [
        {
          id: 'PRE-BOG-06',
          nombre: 'Taller Moto Chapinero',
          tipo: 'taller-motos',
          ramos: ['soat-motocicleta'],
          direccion: 'Cra 13 #45-18',
          ciudad: 'Bogotá',
          pais: 'CO',
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
      truncado: false,
      prestadores: [
        jasmine.objectContaining({ id: 'PRE-BOG-06', pais: 'CO', lat: 4.6355, lng: -74.0655, distanciaKm: 0.9 }),
        jasmine.objectContaining({ id: 'PRE-BOG-07', pais: 'CO', ramos: [], distanciaKm: null }),
      ],
    });
  });

  it('asks by city and country and omits ramo when the chip is Todos', () => {
    const { gateway, http } = setup();
    let cuerpo: unknown;
    gateway.buscar({ ciudad: 'Lima', pais: 'PE', ramo: null }).subscribe((r) => (cuerpo = r));
    const req = http.expectOne((call) => call.url === '/web/cliente/prestadores');
    expect(req.request.params.get('ciudad')).toBe('Lima');
    expect(req.request.params.get('pais')).toBe('PE');
    expect(req.request.params.has('lat')).toBeFalse();
    expect(req.request.params.has('ramo')).toBeFalse();
    expect(req.request.params.has('radioKm')).toBeFalse();
    req.flush({});
    expect(cuerpo).toEqual({ centro: null, radioKm: null, truncado: false, prestadores: [] });
  });

  it('sends the visible area with the origin and ramo, without radius, and maps truncado and pais', () => {
    const { gateway, http } = setup();
    let cuerpo: { truncado: boolean; prestadores: { pais: string }[] } | undefined;
    gateway
      .buscar({ area: CHAPINERO, origen: { lat: 4.6432, lng: -74.0631 }, ramo: 'viaje', pais: 'CO' })
      .subscribe((r) => (cuerpo = r));
    const req = http.expectOne((call) => call.url === '/web/cliente/prestadores');
    expect(req.request.params.get('norte')).toBe('4.66');
    expect(req.request.params.get('sur')).toBe('4.62');
    expect(req.request.params.get('este')).toBe('-74.05');
    expect(req.request.params.get('oeste')).toBe('-74.08');
    expect(req.request.params.get('lat')).toBe('4.6432');
    expect(req.request.params.get('lng')).toBe('-74.0631');
    expect(req.request.params.get('ramo')).toBe('viaje');
    expect(req.request.params.has('radioKm')).toBeFalse();
    expect(req.request.params.has('ciudad')).toBeFalse();
    req.flush({
      centro: null,
      radioKm: null,
      truncado: true,
      prestadores: [
        {
          id: 'PRE-LIM-01',
          nombre: 'Clínica Miraflores',
          tipo: 'ips-urgencias',
          ramos: ['viaje'],
          direccion: 'Av. Larco 100',
          ciudad: 'Lima',
          pais: 'PE',
          barrio: 'Miraflores',
          lat: -12.12,
          lng: -77.03,
          telefono: '1',
          horario: '24 h',
        },
      ],
    });
    expect(cuerpo?.truncado).toBeTrue();
    expect(cuerpo?.prestadores[0].pais).toBe('PE');
  });

  it('sends an area without origin', () => {
    const { gateway, http } = setup();
    gateway.buscar({ area: CHAPINERO }).subscribe();
    const req = http.expectOne((call) => call.url === '/web/cliente/prestadores');
    expect(req.request.params.get('norte')).toBe('4.66');
    expect(req.request.params.has('lat')).toBeFalse();
    req.flush({});
  });

  it('lists the cities of a country with their centers as numbers', () => {
    const { gateway, http } = setup();
    let ciudades: unknown;
    let vacias: unknown;
    gateway.ciudades('CL').subscribe((r) => (ciudades = r));
    http.expectOne('/web/cliente/prestadores/ciudades?pais=CL').flush({
      pais: 'CL',
      ciudades: [
        { nombre: 'Santiago', lat: '-33.448900', lng: '-70.669300', zoom: 11, prestadores: 5 },
      ],
    });
    expect(ciudades).toEqual([
      { nombre: 'Santiago', lat: -33.4489, lng: -70.6693, zoom: 11, prestadores: 5 },
    ]);

    gateway.ciudades('MX').subscribe((r) => (vacias = r));
    http.expectOne('/web/cliente/prestadores/ciudades?pais=MX').flush({ pais: 'MX' });
    expect(vacias).toEqual([]);
  });

  it('maps the real servicio_no_disponible body to an error the view model can retry', () => {
    const { gateway, http } = setup();
    let fallo: unknown;
    let ciudades: unknown;
    gateway.buscar({ ciudad: 'Medellín' }).subscribe({ error: (error) => (fallo = error) });
    http
      .expectOne((call) => call.url === '/web/cliente/prestadores')
      .flush(
        { codigo: 'servicio_no_disponible', mensaje: 'Intenta más tarde' },
        { status: 503, statusText: 'Unavailable' },
      );
    expect(fallo).toBeInstanceOf(ServicioNoDisponible);

    gateway.ciudades('CO').subscribe({ error: (error) => (ciudades = error) });
    http
      .expectOne('/web/cliente/prestadores/ciudades?pais=CO')
      .flush({ codigo: 'servicio_no_disponible' }, { status: 503, statusText: 'Unavailable' });
    expect(ciudades).toBeInstanceOf(ServicioNoDisponible);

    let otro: unknown;
    servicioCaido('red').subscribe({ error: (error) => (otro = error) });
    expect(otro).toBe('red');
  });

  it('passes other failures through, including a 422 area_invalida, and defaults radioKm', () => {
    const { gateway, http } = setup();
    let fallo: unknown;
    gateway.buscar({ origen: { lat: 1, lng: 2 } }).subscribe({ error: (error) => (fallo = error) });
    const req = http.expectOne((call) => call.url === '/web/cliente/prestadores');
    expect(req.request.params.get('radioKm')).toBe('10');
    req.flush({ codigo: 'area_invalida', mensaje: 'x' }, { status: 422, statusText: 'Unprocessable' });
    expect(fallo).not.toBeInstanceOf(ServicioNoDisponible);

    let nulo: unknown;
    gateway.buscar({}).subscribe({ error: (error) => (nulo = error) });
    http
      .expectOne((call) => call.url === '/web/cliente/prestadores')
      .flush(null, { status: 500, statusText: 'Error' });
    expect(nulo).not.toBeInstanceOf(ServicioNoDisponible);
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
        truncado: false,
        prestadores: [],
      }),
    );

    gateway.porSiniestro('ajeno').subscribe((r) => (ajeno = r));
    http
      .expectOne('/web/cliente/siniestros/ajeno/prestadores?radioKm=10')
      .flush({ codigo: 'no_encontrado', mensaje: 'x' }, { status: 404, statusText: 'Not Found' });
    expect(ajeno).toBeNull();
  });

  it('sends the visible area to the claim route instead of the radius', () => {
    const { gateway, http } = setup();
    let truncado: boolean | undefined;
    gateway.porSiniestro('sin-1988', CHAPINERO).subscribe((r) => (truncado = r?.truncado));
    const req = http.expectOne((call) => call.url === '/web/cliente/siniestros/sin-1988/prestadores');
    expect(req.request.params.get('norte')).toBe('4.66');
    expect(req.request.params.get('oeste')).toBe('-74.08');
    expect(req.request.params.has('radioKm')).toBeFalse();
    req.flush({
      siniestro: { id: 'sin-1988', numero: 'SIN-1988', ramo: 'soat-motocicleta' },
      ramoFijo: 'soat-motocicleta',
      sinGeoetiqueta: false,
      centro: { lat: 4.626, lng: -74.15, origen: 'siniestro' },
      radioKm: null,
      truncado: true,
      prestadores: [],
    });
    expect(truncado).toBeTrue();
  });

  it('maps a claim read of servicio_no_disponible to the same error', () => {
    const { gateway, http } = setup();
    let fallo: unknown;
    gateway.porSiniestro('sin-1').subscribe({ error: (error) => (fallo = error) });
    http
      .expectOne('/web/cliente/siniestros/sin-1/prestadores?radioKm=10')
      .flush({ codigo: 'servicio_no_disponible', mensaje: 'x' }, { status: 503, statusText: 'Unavailable' });
    expect(fallo).toBeInstanceOf(ServicioNoDisponible);
  });
});
