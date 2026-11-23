import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { SociosGateway } from './socios.gateway';
import { ACTIVO_ID, VIGENTE_ID } from './socios.testing';

describe('SociosGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return { gateway: TestBed.inject(SociosGateway), http: TestBed.inject(HttpTestingController) };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('lists the partners', () => {
    const { gateway, http } = setup();
    gateway.list().subscribe();
    const lista = http.expectOne('/web/backoffice/socios');
    expect(lista.request.method).toBe('GET');
    lista.flush({ socios: [] });
  });

  it('creates a partner with its name and scopes', () => {
    const { gateway, http } = setup();
    gateway.create({ nombre: 'Aliado', alcances: ['catalogo:leer'] }).subscribe();
    const alta = http.expectOne('/web/backoffice/socios');
    expect(alta.request.method).toBe('POST');
    expect(alta.request.body).toEqual({ nombre: 'Aliado', alcances: ['catalogo:leer'] });
    alta.flush({});
  });

  it('rotates the key of a partner', () => {
    const { gateway, http } = setup();
    gateway.rotate(ACTIVO_ID).subscribe();
    const rotacion = http.expectOne(`/web/backoffice/socios/${ACTIVO_ID}/credenciales`);
    expect(rotacion.request.method).toBe('POST');
    rotacion.flush({ credencialId: VIGENTE_ID, apiKey: 'k' });
  });

  it('revokes one credential of a partner', () => {
    const { gateway, http } = setup();
    gateway.revokeCredential(ACTIVO_ID, VIGENTE_ID).subscribe();
    const baja = http.expectOne(`/web/backoffice/socios/${ACTIVO_ID}/credenciales/${VIGENTE_ID}`);
    expect(baja.request.method).toBe('DELETE');
    baja.flush(null, { status: 204, statusText: 'No Content' });
  });

  it('revokes a partner', () => {
    const { gateway, http } = setup();
    gateway.revoke(ACTIVO_ID).subscribe();
    const revocacion = http.expectOne(`/web/backoffice/socios/${ACTIVO_ID}/revocacion`);
    expect(revocacion.request.method).toBe('POST');
    revocacion.flush({});
  });
});
