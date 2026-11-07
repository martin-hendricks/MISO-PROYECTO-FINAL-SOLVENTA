import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { PolizaBackofficeDetalleView } from './poliza-backoffice-detalle.view';

const POLIZA_WIRE = {
  numero: 'POL-2026-00000001',
  ramo: 'Protección de dispositivo',
  estado: 'vigente',
  venceEn: '2027-10-01',
  prima: { valor: '1000.00', periodicidad: 'ANUAL' },
  renovable: true,
  devolucionEstimada: null,
  canceladaEn: null,
  canceladaPor: null,
  motivoCancelacion: null,
  siniestrosAbiertos: null,
  coberturas: [{ nombre: 'Robo', suma_asegurada: '2000000.00', deducible: '0.00' }],
};

const POLIZA_CANCELADA_WIRE = {
  ...POLIZA_WIRE,
  estado: 'cancelada',
  renovable: false,
  devolucionEstimada: '500.00',
  canceladaEn: '2026-11-01',
  canceladaPor: 'persona@solventa.com',
  motivoCancelacion: 'El cliente lo pidió',
};

describe('PolizaBackofficeDetalleView', () => {
  const URL = '/web/operador/polizas/POL-2026-00000001';
  const CICLO_URL = '/web/operador/polizas/ciclo';

  function render(role: Role = 'operador', numero: string | null = 'POL-2026-00000001') {
    TestBed.configureTestingModule({
      imports: [PolizaBackofficeDetalleView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap(numero ? { numero } : {}) } },
        },
      ],
    });
    const fixture = TestBed.createComponent(PolizaBackofficeDetalleView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) => host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('loads the policy by number from the route', () => {
    const { http, element } = render();

    const request = http.expectOne(URL);
    expect(request.request.method).toBe('GET');
    expect(element('poliza-backoffice-loading')).not.toBeNull();
    request.flush(POLIZA_WIRE);
  });

  it('shows the policy state, vigencia and prima', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(POLIZA_WIRE);
    fixture.detectChanges();

    expect(element('poliza-backoffice-numero')?.textContent).toContain('POL-2026-00000001');
    expect(element('poliza-backoffice-estado')?.getAttribute('data-estado')).toBe('vigente');
    expect(element('poliza-backoffice-prima')?.textContent).toContain('1.000');
  });

  it('shows the open-claims count when the BFF reports one', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ ...POLIZA_WIRE, siniestrosAbiertos: 2 });
    fixture.detectChanges();

    expect(element('poliza-backoffice-siniestros-abiertos')?.textContent).toContain('2');
  });

  it('reports a missing policy as not found', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(null, { status: 404, statusText: 'Not Found' });
    fixture.detectChanges();

    expect(element('poliza-backoffice-not-found')).not.toBeNull();
  });

  it('a load failure is retryable', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    expect(element('poliza-backoffice-error')).not.toBeNull();
    element('poliza-backoffice-retry')!.click();
    http.expectOne(URL).flush(POLIZA_WIRE);
    fixture.detectChanges();

    expect(element('poliza-backoffice-error')).toBeNull();
    expect(element('poliza-backoffice-numero')).not.toBeNull();
  });

  it('renueva a vigente policy that is renovable', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(POLIZA_WIRE);
    fixture.detectChanges();

    const renovar = element('poliza-backoffice-renovar') as HTMLButtonElement;
    expect(renovar.disabled).toBeFalse();
    renovar.click();
    fixture.detectChanges();

    const request = http.expectOne(CICLO_URL);
    expect(request.request.body).toEqual({ numero: 'POL-2026-00000001', verbo: 'renovar' });
    request.flush({ ...POLIZA_WIRE, venceEn: '2028-10-01' });
    fixture.detectChanges();

    expect(element('poliza-backoffice-vence')?.textContent).toContain('2028');
  });

  it('disables Renovar when the core marks the policy as not renovable', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ ...POLIZA_WIRE, renovable: false });
    fixture.detectChanges();

    expect((element('poliza-backoffice-renovar') as HTMLButtonElement).disabled).toBeTrue();
    expect(element('poliza-backoffice-no-renovable')).not.toBeNull();
  });

  it('cancelled policies show the previous cancellation record and disable both actions', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(POLIZA_CANCELADA_WIRE);
    fixture.detectChanges();

    expect(element('poliza-backoffice-estado')?.getAttribute('data-estado')).toBe('cancelada');
    const previa = element('poliza-backoffice-cancelacion-previa')!.textContent!;
    expect(previa).toContain('El cliente lo pidió');
    expect(previa).toContain('persona@solventa.com');
    expect((element('poliza-backoffice-renovar') as HTMLButtonElement).disabled).toBeTrue();
    expect((element('poliza-backoffice-cancelar') as HTMLButtonElement).disabled).toBeTrue();
  });

  it('a cancelled policy without an estimated refund does not render that row', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ ...POLIZA_CANCELADA_WIRE, devolucionEstimada: null });
    fixture.detectChanges();

    expect(element('poliza-backoffice-cancelacion-previa')!.textContent).not.toContain(
      'Devolución estimada',
    );
  });

  it('opens the confirm dialog and cancels with the typed reason', () => {
    const { fixture, http, element, host } = render();
    http.expectOne(URL).flush(POLIZA_WIRE);
    fixture.detectChanges();

    element('poliza-backoffice-cancelar')!.click();
    fixture.detectChanges();
    expect(host.querySelector('[data-testid="confirm-dialog"]')).not.toBeNull();

    const motivo = host.querySelector<HTMLTextAreaElement>('[data-testid="confirm-dialog-motivo"]')!;
    motivo.value = 'El cliente lo pidió';
    motivo.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    host.querySelector<HTMLButtonElement>('[data-testid="confirm-dialog-confirmar"]')!.click();
    fixture.detectChanges();

    const request = http.expectOne(CICLO_URL);
    expect(request.request.body).toEqual({
      numero: 'POL-2026-00000001',
      verbo: 'cancelar',
      motivo: 'El cliente lo pidió',
    });
    request.flush(POLIZA_CANCELADA_WIRE);
    fixture.detectChanges();

    expect(host.querySelector('[data-testid="confirm-dialog"]')).toBeNull();
    expect(element('poliza-backoffice-estado')?.getAttribute('data-estado')).toBe('cancelada');
  });

  it('closing the confirm dialog without confirming does not call the BFF', () => {
    const { fixture, http, element, host } = render();
    http.expectOne(URL).flush(POLIZA_WIRE);
    fixture.detectChanges();

    element('poliza-backoffice-cancelar')!.click();
    fixture.detectChanges();
    host.querySelector<HTMLButtonElement>('[data-testid="confirm-dialog-cancelar"]')!.click();
    fixture.detectChanges();

    expect(host.querySelector('[data-testid="confirm-dialog"]')).toBeNull();
    http.expectNone(CICLO_URL);
  });

  it('a 409 rejection on cancelar shows the core message without closing the dialog state silently', () => {
    const { fixture, http, element, host } = render();
    http.expectOne(URL).flush(POLIZA_WIRE);
    fixture.detectChanges();

    element('poliza-backoffice-cancelar')!.click();
    fixture.detectChanges();
    const motivo = host.querySelector<HTMLTextAreaElement>('[data-testid="confirm-dialog-motivo"]')!;
    motivo.value = 'Otro motivo';
    motivo.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    host.querySelector<HTMLButtonElement>('[data-testid="confirm-dialog-confirmar"]')!.click();
    fixture.detectChanges();

    http
      .expectOne(CICLO_URL)
      .flush({ codigo: 'transicion_invalida', mensaje: 'La póliza ya estaba cancelada' }, { status: 409, statusText: 'Conflict' });
    fixture.detectChanges();

    expect(element('poliza-backoffice-rechazo')?.textContent).toContain('La póliza ya estaba cancelada');
  });

  it('typing a number and searching navigates to its detail route', () => {
    const { fixture, http, element } = render('operador', null);
    const router = TestBed.inject(Router);
    const navigateSpy = spyOn(router, 'navigate');
    http.expectNone(URL);

    const input = element('poliza-backoffice-buscar') as HTMLInputElement;
    input.value = 'POL-2026-00000002';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    fixture.detectChanges();
    element('poliza-backoffice-buscar-submit')!.click();

    expect(navigateSpy).toHaveBeenCalledWith(['/cms/polizas', 'POL-2026-00000002']);
  });

  it('pressing enter in the search field also navigates', () => {
    const { fixture, http, element } = render('operador', null);
    const router = TestBed.inject(Router);
    const navigateSpy = spyOn(router, 'navigate');
    http.expectNone(URL);

    const input = element('poliza-backoffice-buscar') as HTMLInputElement;
    input.value = '  POL-2026-00000003  ';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    fixture.detectChanges();
    input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter' }));

    expect(navigateSpy).toHaveBeenCalledWith(['/cms/polizas', 'POL-2026-00000003']);
  });

  it('searching with a blank number does not navigate', () => {
    const { element } = render('operador', null);
    const router = TestBed.inject(Router);
    const navigateSpy = spyOn(router, 'navigate');

    element('poliza-backoffice-buscar-submit')!.click();

    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it('shows the current coverages', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(POLIZA_WIRE);
    fixture.detectChanges();

    const texto = element('poliza-backoffice-coberturas')!.textContent!;
    expect(texto).toContain('Robo');
  });

  it('shows the empty-coverages hint when the policy has none', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ ...POLIZA_WIRE, coberturas: [] });
    fixture.detectChanges();

    expect(element('poliza-backoffice-coberturas')!.textContent).toContain(
      'no tiene coberturas registradas',
    );
  });

  it('opens the coverage editor pre-filled with the current coverages and saves the change', () => {
    const { fixture, http, element, host } = render();
    http.expectOne(URL).flush(POLIZA_WIRE);
    fixture.detectChanges();

    element('poliza-backoffice-modificar')!.click();
    fixture.detectChanges();

    const nombre = host.querySelector<HTMLInputElement>('[data-testid="poliza-backoffice-cobertura-nombre-0"]')!;
    expect(nombre.value).toBe('Robo');

    nombre.value = 'Robo total';
    nombre.dispatchEvent(new Event('input'));
    const deducible = host.querySelector<HTMLInputElement>(
      '[data-testid="poliza-backoffice-cobertura-deducible-0"]',
    )!;
    deducible.value = '100000';
    deducible.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    element('poliza-backoffice-coberturas-guardar')!.click();
    fixture.detectChanges();

    const request = http.expectOne(CICLO_URL);
    expect(request.request.body).toEqual({
      numero: 'POL-2026-00000001',
      verbo: 'modificar',
      coberturas: [{ nombre: 'Robo total', suma_asegurada: 2000000, deducible: 100000 }],
    });
    request.flush({ ...POLIZA_WIRE, coberturas: [{ nombre: 'Robo total', suma_asegurada: '2000000.00', deducible: '0.00' }] });
    fixture.detectChanges();

    expect(element('poliza-backoffice-coberturas-form')).toBeNull();
    expect(element('poliza-backoffice-coberturas')!.textContent).toContain('Robo total');
  });

  it('adds and removes coverage rows in the editor', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ ...POLIZA_WIRE, coberturas: [] });
    fixture.detectChanges();

    element('poliza-backoffice-modificar')!.click();
    fixture.detectChanges();
    expect(element('poliza-backoffice-cobertura-nombre-0')).toBeNull();

    element('poliza-backoffice-cobertura-agregar')!.click();
    fixture.detectChanges();
    expect(element('poliza-backoffice-cobertura-nombre-0')).not.toBeNull();

    element('poliza-backoffice-cobertura-quitar-0')!.click();
    fixture.detectChanges();
    expect(element('poliza-backoffice-cobertura-nombre-0')).toBeNull();
  });

  it('cannot save coverages with a blank name', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ ...POLIZA_WIRE, coberturas: [] });
    fixture.detectChanges();

    element('poliza-backoffice-modificar')!.click();
    fixture.detectChanges();
    element('poliza-backoffice-cobertura-agregar')!.click();
    fixture.detectChanges();

    expect((element('poliza-backoffice-coberturas-guardar') as HTMLButtonElement).disabled).toBeTrue();

    // El guard también protege una invocación directa del método (no solo
    // el disabled del botón, que podría no respetarse desde otro disparador).
    (fixture.componentInstance as unknown as { guardarCoberturas(): void }).guardarCoberturas();
    http.expectNone(CICLO_URL);
  });

  it('opening the editor for a policy with no coverages starts from an empty list', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ ...POLIZA_WIRE, coberturas: [] });
    fixture.detectChanges();

    element('poliza-backoffice-modificar')!.click();
    fixture.detectChanges();

    expect(element('poliza-backoffice-cobertura-nombre-0')).toBeNull();
  });

  it('editing one row among several only updates that row', () => {
    const { fixture, http, element } = render();
    http
      .expectOne(URL)
      .flush({
        ...POLIZA_WIRE,
        coberturas: [
          { nombre: 'Robo', suma_asegurada: '2000000.00', deducible: '0.00' },
          { nombre: 'Pantalla', suma_asegurada: '500000.00', deducible: '50000.00' },
        ],
      });
    fixture.detectChanges();

    element('poliza-backoffice-modificar')!.click();
    fixture.detectChanges();

    const segundaFila = element('poliza-backoffice-cobertura-nombre-1') as HTMLInputElement;
    segundaFila.value = 'Pantalla rota';
    segundaFila.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect((element('poliza-backoffice-cobertura-nombre-0') as HTMLInputElement).value).toBe('Robo');
    expect(segundaFila.value).toBe('Pantalla rota');
  });

  it('a non-numeric amount is sent as zero instead of NaN', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ ...POLIZA_WIRE, coberturas: [] });
    fixture.detectChanges();

    element('poliza-backoffice-modificar')!.click();
    fixture.detectChanges();
    element('poliza-backoffice-cobertura-agregar')!.click();
    fixture.detectChanges();

    const nombre = element('poliza-backoffice-cobertura-nombre-0') as HTMLInputElement;
    nombre.value = 'Robo';
    nombre.dispatchEvent(new Event('input'));
    const suma = element('poliza-backoffice-cobertura-suma-0') as HTMLInputElement;
    suma.value = '';
    suma.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    element('poliza-backoffice-coberturas-guardar')!.click();

    const request = http.expectOne(CICLO_URL);
    expect((request.request.body as { coberturas: { suma_asegurada: number }[] }).coberturas[0].suma_asegurada).toBe(0);
    request.flush(POLIZA_WIRE);
  });

  it('closing the coverage editor without saving does not call the BFF', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush(POLIZA_WIRE);
    fixture.detectChanges();

    element('poliza-backoffice-modificar')!.click();
    fixture.detectChanges();
    element('poliza-backoffice-coberturas-cancelar')!.click();
    fixture.detectChanges();

    expect(element('poliza-backoffice-coberturas-form')).toBeNull();
    http.expectNone(CICLO_URL);
  });

  it('keeps the section from the advisor without calling the BFF', () => {
    const { http, element } = render('asesor');

    http.expectNone(URL);
    expect(element('poliza-backoffice')?.getAttribute('data-state')).toBe('no-permission');
    expect(element('no-permission')?.getAttribute('data-required')).toBe('operador');
  });
});
