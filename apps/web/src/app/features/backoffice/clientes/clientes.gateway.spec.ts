import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ClientesGateway } from './clientes.gateway';

describe('ClientesGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return { gateway: TestBed.inject(ClientesGateway), http: TestBed.inject(HttpTestingController) };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('lists with search and status, and omits a query shorter than two characters', () => {
    const { gateway, http } = setup();
    gateway.list({ q: ' Ana ', estado: 'ACTIVO', pagina: 2 }).subscribe();
    const filtrada = http.expectOne((request) => request.url === '/web/operador/clientes');
    expect(filtrada.request.params.get('q')).toBe('Ana');
    expect(filtrada.request.params.get('estado')).toBe('ACTIVO');
    expect(filtrada.request.params.get('pagina')).toBe('2');
    filtrada.flush({ clientes: [], pagina: 2, hayMas: false });

    gateway.list({ q: 'a', estado: '', pagina: 1 }).subscribe();
    const corta = http.expectOne((request) => request.url === '/web/operador/clientes');
    expect(corta.request.params.has('q')).toBeFalse();
    expect(corta.request.params.has('estado')).toBeFalse();
    corta.flush({ clientes: [], pagina: 1, hayMas: false });
  });

  it('creates, edits and changes status', () => {
    const { gateway, http } = setup();
    const id = '11111111-1111-4111-8111-111111111111';
    gateway
      .create({
        tipoDocumento: 'CC',
        documento: '1',
        email: 'ana@correo.com',
        password: 'secreto',
        nombre: 'Ana',
        apellidos: 'Ruiz',
      })
      .subscribe();
    const alta = http.expectOne('/web/operador/clientes');
    expect(alta.request.method).toBe('POST');
    alta.flush({});

    gateway.update(id, { nombre: 'Ana', apellidos: 'Ruiz', email: 'nueva@correo.com' }).subscribe();
    const edicion = http.expectOne(`/web/operador/clientes/${id}`);
    expect(edicion.request.method).toBe('PATCH');
    edicion.flush({});

    gateway.setEstado(id, 'INACTIVO').subscribe();
    const estado = http.expectOne(`/web/operador/clientes/${id}/estado`);
    expect(estado.request.body).toEqual({ estado: 'INACTIVO' });
    estado.flush({});
  });
});
