import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { EmisionGateway } from './emision.gateway';

describe('EmisionGateway', () => {
  afterEach(() => localStorage.removeItem('solventa.locale'));

  function accept(locale?: string) {
    if (locale) localStorage.setItem('solventa.locale', locale);
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), ...provideSolventaI18n()],
    });
    const http = TestBed.inject(HttpTestingController);
    TestBed.inject(EmisionGateway).accept({ cotizacionId: 'COT-1042' }).subscribe();
    const request = http.expectOne('/web/cliente/polizas');
    return { http, request };
  }

  it('accepts with the quote id, the locale currency, and no card fields', () => {
    const { http, request } = accept();
    expect(request.request.body).toEqual({ cotizacionId: 'COT-1042', monedaInicio: 'COP' });
    expect(JSON.stringify(request.request.body)).not.toContain('tarjeta');
    request.flush({ resultado: 'EMITIDA', poliza: { numero: 'POL-1', referenciaPago: 'PAY-44218' } });
    http.verify();
  });

  it('sends MXN when the active locale is es-MX', () => {
    const { http, request } = accept('es-MX');
    expect(request.request.body).toEqual({ cotizacionId: 'COT-1042', monedaInicio: 'MXN' });
    request.flush({ resultado: 'EMITIDA', poliza: { numero: 'POL-1', referenciaPago: 'PAY-44218' } });
    http.verify();
  });
});
