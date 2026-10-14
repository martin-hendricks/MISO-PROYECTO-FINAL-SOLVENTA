import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { FORMULARIO, OFERTA } from './cotizacion.testing';
import { CotizacionView } from './cotizacion.view';

describe('CotizacionView', () => {
  const URL = '/web/asesor/cotizaciones';

  function render(role: Role) {
    TestBed.configureTestingModule({
      imports: [CotizacionView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
      ],
    });
    const fixture = TestBed.createComponent(CotizacionView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = <T extends HTMLElement = HTMLElement>(testId: string) =>
      host.querySelector<T>(`[data-testid="${testId}"]`);
    const type = (testId: string, value: string) => {
      const input = element<HTMLInputElement>(testId)!;
      input.value = value;
      input.dispatchEvent(new Event('input'));
      fixture.detectChanges();
    };
    const fill = () => {
      type('cotizacion-nombre', FORMULARIO.nombre);
      type('cotizacion-documento', FORMULARIO.documento);
      type('cotizacion-valor', FORMULARIO.valorAsegurado);
      type('cotizacion-marca', FORMULARIO.marca);
      type('cotizacion-modelo', FORMULARIO.modelo);
    };
    const calculate = () => {
      element('cotizacion-calcular')!.click();
      fixture.detectChanges();
    };
    return { fixture, http, host, element, type, fill, calculate };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('opens with the form, the device line and no offer', () => {
    const { host, element } = render('asesor');

    expect(host.querySelector('h1')?.textContent).toContain('Nueva cotización · Dispositivo');
    expect(host.querySelectorAll('legend')[1].textContent).toContain(
      'Datos del riesgo · dispositivo',
    );
    expect(element('cotizacion-back')?.getAttribute('href')).toBe('/cms/cotizaciones');
    expect(element('cotizacion-ramo-dispositivo')?.getAttribute('aria-pressed')).toBe('true');
    expect(element<HTMLButtonElement>('cotizacion-ramo-viaje')?.disabled).toBeTrue();
    expect(element<HTMLButtonElement>('cotizacion-calcular')?.disabled).toBeTrue();
    expect(element('cotizacion-sin-oferta')?.textContent).toContain('Completa los datos');
    expect(element('cotizacion-oferta')).toBeNull();
  });

  it('shows the firm offer with the amounts in the locale format', () => {
    const { fixture, http, element, fill, calculate } = render('asesor');
    fill();

    calculate();
    const request = http.expectOne(URL);
    expect(request.request.method).toBe('POST');
    expect(request.request.body.datosRiesgo.valorAsegurado).toBe(1200000);
    expect(element<HTMLButtonElement>('cotizacion-calcular')?.disabled).toBeTrue();
    request.flush(OFERTA);
    fixture.detectChanges();

    expect(element('cotizacion-oferta')?.getAttribute('data-cotizacion-id')).toBe('COT-1042');
    expect(element('oferta-prima')?.textContent).toBe('$89.000 COP');
    expect(element('oferta-prima-neta')?.textContent).toBe('$72.500');
    expect(element('oferta-gastos')?.textContent).toBe('$16.500');
    expect(element('oferta-vigencia')?.textContent?.trim()).toBe('12 meses');
    expect(element('oferta-vence')?.textContent).toBe('01/10/2026');
    expect(element('cotizacion-emitir')?.getAttribute('href')).toBe(
      '/cms/polizas?cotizacion=COT-1042',
    );
    expect(element<HTMLButtonElement>('cotizacion-enviar')?.disabled).toBeTrue();
    expect(element('cotizacion-sin-oferta')).toBeNull();
  });

  it('reads the quote by id when the advisor asks again without changes', () => {
    const { fixture, http, element, fill, calculate } = render('asesor');
    fill();
    calculate();
    http.expectOne(URL).flush(OFERTA);
    fixture.detectChanges();

    calculate();
    const again = http.expectOne(`${URL}/COT-1042`);
    expect(again.request.method).toBe('GET');
    again.flush(OFERTA);
    fixture.detectChanges();

    expect(element('oferta-prima')?.textContent).toBe('$89.000 COP');
  });

  it('solves an insured value out of range in the same view', () => {
    const { http, element, type, fill } = render('asesor');
    fill();

    type('cotizacion-valor', '0');

    const valor = element<HTMLInputElement>('cotizacion-valor')!;
    expect(valor.getAttribute('aria-invalid')).toBe('true');
    expect(valor.getAttribute('aria-describedby')).toBe('cotizacion-valor-error');
    expect(element('cotizacion-valor-error')?.textContent?.trim()).toBe(
      'El valor asegurado debe estar entre $200.000 y $8.000.000 COP.',
    );
    expect(element<HTMLButtonElement>('cotizacion-calcular')?.disabled).toBeTrue();
    expect(element('cotizacion-sin-oferta')?.textContent).toContain('Corrige los datos del riesgo');
    expect(element<HTMLInputElement>('cotizacion-nombre')?.value).toBe(FORMULARIO.nombre);
    expect(element<HTMLInputElement>('cotizacion-modelo')?.value).toBe(FORMULARIO.modelo);
    http.expectNone(URL);
  });

  it('drops the offer when the risk changes after pricing', () => {
    const { fixture, http, element, type, fill, calculate } = render('asesor');
    fill();
    calculate();
    http.expectOne(URL).flush(OFERTA);
    fixture.detectChanges();

    type('cotizacion-valor', '0');

    expect(element('cotizacion-oferta')).toBeNull();
    expect(element('cotizacion-emitir')).toBeNull();
    expect(element('cotizacion-sin-oferta')).not.toBeNull();
  });

  it('keeps issuance off for an offer that is no longer in force', () => {
    const { fixture, http, element, fill, calculate } = render('asesor');
    fill();
    calculate();
    http.expectOne(URL).flush({ ...OFERTA, estado: 'oferta_vencida' });
    fixture.detectChanges();

    const emitir = element<HTMLButtonElement>('cotizacion-emitir')!;
    expect(emitir.tagName).toBe('BUTTON');
    expect(emitir.disabled).toBeTrue();
  });

  it('sends the chosen term and device type', () => {
    const { http, element, fill, calculate } = render('asesor');
    fill();
    for (const [testId, value] of [
      ['cotizacion-vigencia', '24'],
      ['cotizacion-tipo', 'tablet'],
    ]) {
      const select = element<HTMLSelectElement>(testId)!;
      select.value = value;
      select.dispatchEvent(new Event('change'));
    }

    calculate();

    const body = http.expectOne(URL).request.body;
    expect(body.vigenciaMeses).toBe(24);
    expect(body.datosRiesgo.tipo).toBe('tablet');
  });

  it('reports a failure without losing the form and lets the advisor retry', () => {
    const { fixture, http, element, fill, calculate } = render('asesor');
    fill();
    calculate();
    http.expectOne(URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    expect(element('cotizacion-error')).not.toBeNull();
    expect(element<HTMLInputElement>('cotizacion-marca')?.value).toBe(FORMULARIO.marca);

    calculate();
    http.expectOne(URL).flush(OFERTA);
    fixture.detectChanges();

    expect(element('cotizacion-error')).toBeNull();
    expect(element('cotizacion-oferta')).not.toBeNull();
  });

  it('clears the form and the offer', () => {
    const { fixture, http, element, fill, calculate } = render('asesor');
    fill();
    calculate();
    http.expectOne(URL).flush(OFERTA);
    fixture.detectChanges();

    element('cotizacion-limpiar')!.click();
    fixture.detectChanges();

    expect(element<HTMLInputElement>('cotizacion-nombre')?.value).toBe('');
    expect(element('cotizacion-oferta')).toBeNull();
  });

  it('keeps the quote form from the operator', () => {
    const { http, element } = render('operador');

    http.expectNone(URL);
    expect(element('section-cotizacion')?.getAttribute('data-state')).toBe('no-permission');
    expect(element('no-permission')?.getAttribute('data-required')).toBe('asesor');
    expect(element('cotizacion-form')).toBeNull();
  });
});
