import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { INICIO, INICIO_VACIO } from './inicio.testing';
import { InicioView } from './inicio.view';
import { InicioViewModel } from './inicio.viewmodel';

describe('InicioView', () => {
  const URL = '/web/cliente/inicio';

  function render() {
    TestBed.configureTestingModule({
      imports: [InicioView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
      ],
    });
    const fixture = TestBed.createComponent(InicioView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('shows the cards of the aggregate with their shortcuts', () => {
    const { fixture, http, host, element } = render();

    expect(element('inicio-loading')).not.toBeNull();
    http.expectOne(URL).flush(INICIO);
    fixture.detectChanges();

    const offers = host.querySelectorAll('[data-testid="inicio-offer"]');
    const claims = host.querySelectorAll('[data-testid="inicio-claim"]');
    expect(offers.length).toBe(1);
    expect(claims.length).toBe(1);
    expect(element('inicio-offer-summary')).toBeNull();
    expect(element('inicio-offer')?.textContent).toContain(
      'Paso 2 de 4 · Cotización lista: acéptala para emitir',
    );
    expect(element('inicio-offer')?.textContent).toContain('Protección de dispositivo');
    expect(element('inicio-offer')?.textContent).toContain('2999');
    expect(element('inicio-accept')?.textContent).toContain('Aceptar y emitir');
    expect(element('inicio-accept')?.getAttribute('href')).toBe(
      '/confirmacion-tarjeta?cotizacion=COT-1042',
    );
    expect(element('inicio-offer-detail')?.textContent).toContain('Ver detalle');
    expect(element('inicio-offer-detail')?.getAttribute('href')).toBe('/cotizaciones/COT-1042');
    expect(element('inicio-policy')?.textContent).toContain('Póliza vigente');
    expect(element('inicio-policy')?.textContent).toContain('Vigente');
    expect(element('inicio-policy-link')?.getAttribute('href')).toBe('/polizas/POL-88219-CO');
    expect(element('inicio-claim')?.textContent).toContain('SIN-441');
    expect(element('inicio-claim')?.textContent).toContain('En evaluación');
    expect(element('inicio-claim-link')?.textContent).toContain('Ir a siniestros');
    expect(element('inicio-claim-link')?.getAttribute('href')).toBe('/siniestros/SIN-441');
    expect(element('inicio-vida-crediticia')?.textContent).toContain('Vida hipotecario');
    expect(element('inicio-vida-crediticia')?.textContent).toContain('Disponible');
    expect(element('inicio-vida-link')?.getAttribute('href')).toBe('/vida-crediticia');
  });

  it('keeps "Nueva cotización" in the page head while the offer can be accepted', () => {
    const { fixture, http, host, element } = render();

    http.expectOne(URL).flush(INICIO);
    fixture.detectChanges();

    const quotes = host.querySelectorAll('[data-testid="inicio-new-quote"]');
    const accept = element('inicio-accept')!;
    expect(quotes.length).toBe(1);
    expect(quotes[0].textContent).toContain('Nueva cotización');
    expect(
      quotes[0].compareDocumentPosition(accept) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(quotes[0].getAttribute('href')).toBe('/cotizacion');
  });

  it('offers a quote from the head when there is no valid offer', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush({ ...INICIO, ofertaVigente: null, hipotecario: null });
    fixture.detectChanges();

    expect(element('inicio-offer')).toBeNull();
    expect(element('inicio-accept')).toBeNull();
    expect(element('inicio-vida-crediticia')).toBeNull();
    expect(element('inicio-new-quote')?.getAttribute('href')).toBe('/cotizacion');
  });

  it('draws only the cards whose block is present', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush({ ...INICIO_VACIO, ofertaVigente: INICIO.ofertaVigente });
    fixture.detectChanges();

    expect(element('inicio-offer')).not.toBeNull();
    expect(element('inicio-policy')).toBeNull();
    expect(element('inicio-claim')).toBeNull();
    expect(element('inicio-vida-crediticia')).toBeNull();
  });

  it('draws the side column when only Vida hipotecario is present', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush({ ...INICIO_VACIO, hipotecario: INICIO.hipotecario });
    fixture.detectChanges();

    expect(element('inicio-offer')).toBeNull();
    expect(element('inicio-vida-crediticia')).not.toBeNull();
    expect(element('inicio-claim')).toBeNull();
  });

  it('draws the policy summary without the detail row', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush({ ...INICIO_VACIO, poliza: INICIO.poliza });
    fixture.detectChanges();

    expect(element('inicio-policy')).not.toBeNull();
    expect(element('inicio-offer')).toBeNull();
    expect(element('inicio-vida-crediticia')).toBeNull();
    expect(element('inicio-claim')).toBeNull();
  });

  it('stays blank until the aggregate arrives', () => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    const vm = new InicioViewModel(() => {
      throw new Error('not loaded');
    });

    expect(vm.panel()).toEqual({
      offer: null,
      policy: null,
      claim: null,
      vidaCrediticia: false,
    });
    expect(vm.status()).toBe('loading');
  });

  it('shows the empty state when there are no cards', () => {
    const { fixture, http, element } = render();

    http.expectOne(URL).flush(INICIO_VACIO);
    fixture.detectChanges();

    expect(element('inicio')?.getAttribute('data-state')).toBe('empty');
    expect(element('inicio-empty')).not.toBeNull();
    expect(element('inicio-new-quote')).not.toBeNull();
  });

  it('offers to retry in the same view when the aggregate fails', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    element('inicio-retry')!.click();
    http.expectOne(URL).flush(INICIO);
    fixture.detectChanges();

    expect(element('inicio-error')).toBeNull();
    expect(element('inicio-offer')).not.toBeNull();
  });
});
