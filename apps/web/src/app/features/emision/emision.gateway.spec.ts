import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { EmisionGateway } from './emision.gateway';

describe('EmisionGateway', () => {
  it('accepts with the quote id and no card fields', () => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    const http = TestBed.inject(HttpTestingController);
    TestBed.inject(EmisionGateway).accept({ cotizacionId: 'COT-1042' }).subscribe();
    const request = http.expectOne('/web/cliente/polizas');
    expect(request.request.body).toEqual({ cotizacionId: 'COT-1042' });
    expect(JSON.stringify(request.request.body)).not.toContain('tarjeta');
    request.flush({ resultado: 'EMITIDA', poliza: { numero: 'POL-1', referenciaPago: 'PAY-44218' } });
    http.verify();
  });
});
