import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { RECHAZADO } from '../siniestros.testing';
import { SiniestroDetalleView } from './siniestro-detalle.view';

describe('SiniestroDetalleView', () => {
  const ID = RECHAZADO.id;

  function render() {
    TestBed.configureTestingModule({
      imports: [SiniestroDetalleView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ id: ID }) } },
        },
      ],
    });
    const fixture = TestBed.createComponent(SiniestroDetalleView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (id: string) => host.querySelector<HTMLElement>(`[data-testid="${id}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('muestra estado, motivo del rechazo, evidencia e historial en solo lectura', () => {
    const { fixture, http, host, element } = render();
    http.expectOne(`/web/cliente/siniestros/${ID}`).flush(RECHAZADO);
    fixture.detectChanges();

    expect(element('siniestro-estado')?.textContent).toContain('Rechazado');
    expect(element('siniestro-motivo')?.textContent).toContain('falta soporte de la factura');
    expect(element('siniestro-evidencia')?.querySelector('a')?.getAttribute('href')).toBe(
      'https://s3/firmada',
    );
    expect(element('siniestro-historial')?.querySelectorAll('li').length).toBe(3);
    expect(element('siniestro-ver-billetera')).toBeNull();
    expect(host.querySelectorAll('button').length).toBe(0);
  });

  it('muestra el pago, la ubicación y guiones cuando faltan datos', () => {
    const { fixture, http, element } = render();
    http.expectOne(`/web/cliente/siniestros/${ID}`).flush({
      ...RECHAZADO,
      estado: 'pagado',
      resultado: 'aprobado',
      motivo: null,
      poliza: null,
      fecha: null,
      descripcion: null,
      reserva: null,
      geo: { lat: '4.653300', lng: '-74.083600', precision_m: null },
      evidencia: [],
      pago: { comprobante: 'CMP-1', monto: 420000, moneda: 'COP', fecha: '2026-11-02T12:00:00Z' },
    });
    fixture.detectChanges();

    expect(element('siniestro-estado')?.textContent).toContain('Pagado');
    expect(element('siniestro-motivo')).toBeNull();
    expect(element('siniestro-pago')?.textContent).toContain('CMP-1');
    expect(element('siniestro-pago')?.textContent).toContain('Ver en billetera');
    expect(element('siniestro-ver-billetera')?.getAttribute('href')).toBe(`/billetera/${ID}`);
    expect(element('siniestro-evidencia')?.textContent).toContain('Sin evidencia');
    expect(element('siniestro-detalle')?.textContent).toContain('4.653300, -74.083600');
  });

  it('si falla la carga permite reintentar', () => {
    const { fixture, http, host, element } = render();
    http
      .expectOne(`/web/cliente/siniestros/${ID}`)
      .flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('siniestro-error')).not.toBeNull();
    (host.querySelector('[data-testid="siniestro-error"] button') as HTMLButtonElement).click();
    http.expectOne(`/web/cliente/siniestros/${ID}`).flush(RECHAZADO);
    fixture.detectChanges();
    expect(element('siniestro-titulo')).not.toBeNull();
  });

  it('un siniestro ajeno o inexistente muestra no encontrado', () => {
    const { fixture, http, element } = render();
    http
      .expectOne(`/web/cliente/siniestros/${ID}`)
      .flush({}, { status: 404, statusText: 'Not Found' });
    fixture.detectChanges();
    expect(element('siniestro-not-found')).not.toBeNull();
  });
});
