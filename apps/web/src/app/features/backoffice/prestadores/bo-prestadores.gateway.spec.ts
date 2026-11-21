import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { BoPrestadoresGateway, PrestadorEntrada } from './bo-prestadores.gateway';

const ENTRADA: PrestadorEntrada = {
  nombre: 'Taller Moto Norte Usaquén',
  tipo: 'taller-motos',
  ramos: ['soat-motocicleta'],
  direccion: 'Cra 7 #120-10',
  pais: 'CO',
  ciudad: 'Bogotá',
  barrio: 'Usaquén',
  lat: 4.7,
  lng: -74.03,
  telefono: '601 555 0199',
  horario: 'Lun–Vie 8:00–18:00',
};

const FILA = {
  ...ENTRADA,
  id: 'PRE-BOG-99',
  estado: 'activo',
  actualizadoEn: '2026-11-17T12:00:00Z',
  lat: '4.700000',
  lng: '-74.030000',
};

describe('BoPrestadoresGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return {
      gateway: TestBed.inject(BoPrestadoresGateway),
      http: TestBed.inject(HttpTestingController),
    };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('lists with filters, counts and camelCase rows', () => {
    const { gateway, http } = setup();
    let cuerpo: unknown;
    gateway
      .listar({ pais: 'CO', ramo: 'soat-motocicleta', ciudad: 'Bogotá', estado: 'activo' })
      .subscribe((r) => (cuerpo = r));
    const req = http.expectOne(
      (call) => call.url === '/web/operador/prestadores' && call.method === 'GET',
    );
    expect(req.request.params.get('pais')).toBe('CO');
    expect(req.request.params.get('ramo')).toBe('soat-motocicleta');
    expect(req.request.params.get('ciudad')).toBe('Bogotá');
    expect(req.request.params.get('estado')).toBe('activo');
    req.flush({
      pais: 'CO',
      conteos: { Bogotá: 30, Medellín: '20', Chía: 0 },
      centro: { lat: '4.6097', lng: '-74.0817', origen: 'ciudad' },
      prestadores: [FILA],
    });
    expect(cuerpo).toEqual({
      pais: 'CO',
      conteos: { Bogotá: 30, Medellín: 20, Chía: 0 },
      centro: { lat: 4.6097, lng: -74.0817 },
      prestadores: [jasmine.objectContaining({ id: 'PRE-BOG-99', lat: 4.7, lng: -74.03, ramos: ['soat-motocicleta'] })],
    });
  });

  it('omits empty filters and defaults a missing catalog', () => {
    const { gateway, http } = setup();
    let cuerpo: unknown;
    gateway.listar().subscribe((r) => (cuerpo = r));
    const req = http.expectOne('/web/operador/prestadores');
    expect(req.request.params.keys().length).toBe(0);
    req.flush({});
    expect(cuerpo).toEqual({ pais: 'CO', conteos: {}, centro: null, prestadores: [] });
  });

  it('keeps counts for any city name of the asked country', () => {
    const { gateway, http } = setup();
    let cuerpo: unknown;
    gateway.listar({ pais: 'CL' }).subscribe((r) => (cuerpo = r));
    http
      .expectOne((call) => call.url === '/web/operador/prestadores' && call.params.get('pais') === 'CL')
      .flush({
        conteos: { Santiago: 7, Valparaíso: 3, Concepción: 0 },
        prestadores: [{ ...FILA, id: 'PRE-SCL-01', pais: 'CL', ciudad: 'Santiago' }],
      });
    expect(cuerpo).toEqual({
      pais: 'CL',
      conteos: { Santiago: 7, Valparaíso: 3, Concepción: 0 },
      centro: null,
      prestadores: [jasmine.objectContaining({ id: 'PRE-SCL-01', pais: 'CL' })],
    });
  });

  it('lists the catalog cities of a country, with or without providers', () => {
    const { gateway, http } = setup();
    let ciudades: unknown;
    gateway.ciudades('CL').subscribe((r) => (ciudades = r));
    const req = http.expectOne(
      (call) => call.url === '/web/operador/prestadores/ciudades' && call.method === 'GET',
    );
    expect(req.request.params.get('pais')).toBe('CL');
    req.flush({
      pais: 'CL',
      ciudades: [
        { nombre: 'Santiago', lat: '-33.448900', lng: '-70.669300', zoom: 11, prestadores: 7 },
        { nombre: 'Concepción', lat: -36.827, lng: -73.0503, zoom: 13, prestadores: 0 },
      ],
    });
    expect(ciudades).toEqual([
      { nombre: 'Santiago', lat: -33.4489, lng: -70.6693, zoom: 11, prestadores: 7 },
      { nombre: 'Concepción', lat: -36.827, lng: -73.0503, zoom: 13, prestadores: 0 },
    ]);

    gateway.ciudades('PE').subscribe((r) => (ciudades = r));
    http.expectOne((call) => call.params.get('pais') === 'PE').flush({});
    expect(ciudades).toEqual([]);
  });

  it('reads one provider and returns null on 404', () => {
    const { gateway, http } = setup();
    let fila: unknown;
    let falta: unknown = 'pendiente';
    gateway.obtener('PRE-BOG-99').subscribe((r) => (fila = r));
    http
      .expectOne('/web/operador/prestadores/PRE-BOG-99')
      .flush({ ...FILA, ramos: undefined, pais: undefined });
    expect(fila).toEqual(
      jasmine.objectContaining({
        id: 'PRE-BOG-99',
        pais: 'CO',
        ramos: [],
        actualizadoEn: FILA.actualizadoEn,
      }),
    );

    gateway.obtener('nope').subscribe((r) => (falta = r));
    http
      .expectOne('/web/operador/prestadores/nope')
      .flush({}, { status: 404, statusText: 'Not Found' });
    expect(falta).toBeNull();
  });

  it('propagates a failed read that is not 404', () => {
    const { gateway, http } = setup();
    let fallo = false;
    gateway.obtener('x').subscribe({ error: () => (fallo = true) });
    http
      .expectOne('/web/operador/prestadores/x')
      .flush({}, { status: 503, statusText: 'Unavailable' });
    expect(fallo).toBeTrue();
  });

  it('creates, edits and changes estado', () => {
    const { gateway, http } = setup();
    const vistos: string[] = [];
    gateway.crear(ENTRADA).subscribe((r) => vistos.push(`crear:${r.id}`));
    const crear = http.expectOne('/web/operador/prestadores');
    expect(crear.request.method).toBe('POST');
    expect(crear.request.body).toEqual(ENTRADA);
    crear.flush(FILA);

    gateway
      .editar('PRE-BOG-99', { ...ENTRADA, pais: 'MX', ramos: ['soat-motocicleta', 'viaje'] })
      .subscribe((r) =>
      vistos.push(`editar:${r.ramos.length}`),
    );
    const editar = http.expectOne('/web/operador/prestadores/PRE-BOG-99');
    expect(editar.request.method).toBe('PATCH');
    expect(editar.request.body.ramos).toEqual(['soat-motocicleta', 'viaje']);
    expect(editar.request.body.pais).toBe('MX');
    editar.flush({ ...FILA, ramos: ['soat-motocicleta', 'viaje'] });

    gateway.cambiarEstado('PRE-BOG-99', 'inactivo').subscribe((r) => vistos.push(r.estado));
    const estado = http.expectOne('/web/operador/prestadores/PRE-BOG-99/estado');
    expect(estado.request.method).toBe('POST');
    expect(estado.request.body).toEqual({ estado: 'inactivo' });
    estado.flush({ ...FILA, estado: 'inactivo', actualizadoEn: undefined });

    expect(vistos).toEqual(['crear:PRE-BOG-99', 'editar:2', 'inactivo']);
  });
});
