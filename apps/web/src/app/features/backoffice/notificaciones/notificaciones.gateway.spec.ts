import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { NotificacionesGateway, usuarioAudiencia } from './notificaciones.gateway';

describe('NotificacionesGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return {
      gateway: TestBed.inject(NotificacionesGateway),
      http: TestBed.inject(HttpTestingController),
    };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('calls the three operator notification routes', () => {
    const { gateway, http } = setup();

    gateway.audiencia().subscribe();
    http.expectOne('/web/operador/notificaciones/audiencia').flush({});

    gateway
      .enviar({
        titulo: 'Aviso',
        cuerpo: 'Texto',
        audiencia: { tipo: 'usuarios', usuarioIds: ['u1'] },
        poliza: 'POL-1',
      })
      .subscribe();
    const enviado = http.expectOne('/web/operador/notificaciones/difusiones');
    expect(enviado.request.method).toBe('POST');
    expect(enviado.request.body).toEqual({
      titulo: 'Aviso',
      cuerpo: 'Texto',
      audiencia: { tipo: 'usuarios', usuarioIds: ['u1'] },
      poliza: 'POL-1',
    });
    enviado.flush({ difusionId: '1', enviadas: 1, fallidas: 0, sinDispositivo: 0 });

    gateway.historial(10, '2026-11-09T13:05:00Z').subscribe();
    const historial = http.expectOne(
      (request) => request.url === '/web/operador/notificaciones/difusiones',
    );
    expect(historial.request.method).toBe('GET');
    expect(historial.request.params.get('limite')).toBe('10');
    expect(historial.request.params.get('antesDe')).toBe('2026-11-09T13:05:00Z');
    historial.flush({ items: [] });
  });

  it('reads the name and the citizen id from either payload shape', () => {
    setup();
    expect(
      usuarioAudiencia({
        usuario_id: '11111111-1111-4111-8111-111111111111',
        nombre: 'Ana',
        apellidos: 'Ruiz',
        correo: 'ana@correo.com',
        numero_documento: '1020334556',
        dispositivos_activos: 1,
      }),
    ).toEqual({
      usuarioId: '11111111-1111-4111-8111-111111111111',
      nombre: 'Ana',
      apellidos: 'Ruiz',
      email: 'ana@correo.com',
      documento: '1020334556',
      dispositivosActivos: 1,
    });
    expect(usuarioAudiencia({ numero_documento: 1020 })).toEqual({
      usuarioId: '',
      nombre: '',
      apellidos: '',
      email: '',
      documento: '1020',
      dispositivosActivos: 0,
    });
  });
});
