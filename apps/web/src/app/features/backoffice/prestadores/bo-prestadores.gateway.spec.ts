import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { BoPrestadoresGateway, PrestadorEntrada } from './bo-prestadores.gateway';

const ENTRADA: PrestadorEntrada = {
  nombre: 'Taller Moto Norte Usaquén',
  tipo: 'taller-motos',
  ramos: ['soat-motocicleta'],
  direccion: 'Cra 7 #120-10',
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
      .listar({ ramo: 'soat-motocicleta', ciudad: 'Bogotá', estado: 'activo' })
      .subscribe((r) => (cuerpo = r));
    const req = http.expectOne(
      (call) => call.url === '/web/operador/prestadores' && call.method === 'GET',
    );
    expect(req.request.params.get('ramo')).toBe('soat-motocicleta');
    expect(req.request.params.get('ciudad')).toBe('Bogotá');
    expect(req.request.params.get('estado')).toBe('activo');
    req.flush({
      conteos: { Bogotá: 30 },
      centro: { lat: 4.6097, lng: -74.0817 },
      prestadores: [FILA],
    });
    expect(cuerpo).toEqual({
      conteos: { Bogotá: 30, Medellín: 0, Chía: 0 },
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
    expect(cuerpo).toEqual({
      conteos: { Bogotá: 0, Medellín: 0, Chía: 0 },
      centro: null,
      prestadores: [],
    });
  });

  it('reads one provider and returns null on 404', () => {
    const { gateway, http } = setup();
    let fila: unknown;
    let falta: unknown = 'pendiente';
    gateway.obtener('PRE-BOG-99').subscribe((r) => (fila = r));
    http.expectOne('/web/operador/prestadores/PRE-BOG-99').flush({ ...FILA, ramos: undefined });
    expect(fila).toEqual(jasmine.objectContaining({ id: 'PRE-BOG-99', ramos: [], actualizadoEn: FILA.actualizadoEn }));

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

    gateway.editar('PRE-BOG-99', { ...ENTRADA, ramos: ['soat-motocicleta', 'viaje'] }).subscribe((r) =>
      vistos.push(`editar:${r.ramos.length}`),
    );
    const editar = http.expectOne('/web/operador/prestadores/PRE-BOG-99');
    expect(editar.request.method).toBe('PATCH');
    expect(editar.request.body.ramos).toEqual(['soat-motocicleta', 'viaje']);
    editar.flush({ ...FILA, ramos: ['soat-motocicleta', 'viaje'] });

    gateway.cambiarEstado('PRE-BOG-99', 'inactivo').subscribe((r) => vistos.push(r.estado));
    const estado = http.expectOne('/web/operador/prestadores/PRE-BOG-99/estado');
    expect(estado.request.method).toBe('POST');
    expect(estado.request.body).toEqual({ estado: 'inactivo' });
    estado.flush({ ...FILA, estado: 'inactivo', actualizadoEn: undefined });

    expect(vistos).toEqual(['crear:PRE-BOG-99', 'editar:2', 'inactivo']);
  });
});
