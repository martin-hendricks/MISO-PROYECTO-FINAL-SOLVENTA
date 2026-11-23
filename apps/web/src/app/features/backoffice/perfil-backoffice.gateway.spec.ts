import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { PerfilBackoffice, PerfilBackofficeGateway } from './perfil-backoffice.gateway';

describe('PerfilBackofficeGateway', () => {
  it('loads the profile of the logged-in asesor/operador', () => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    const http = TestBed.inject(HttpTestingController);
    const perfil = { usuarioId: 'u1', correo: 'jorge@solventa.co', nombre: 'Jorge', apellidos: 'Nieto', rol: 'operador' };

    let recibido: PerfilBackoffice | undefined;
    TestBed.inject(PerfilBackofficeGateway)
      .load()
      .subscribe((respuesta) => (recibido = respuesta));

    const request = http.expectOne('/web/backoffice/perfil');
    expect(request.request.method).toBe('GET');
    request.flush(perfil);

    expect(recibido).toEqual(perfil);
    http.verify();
  });
});
