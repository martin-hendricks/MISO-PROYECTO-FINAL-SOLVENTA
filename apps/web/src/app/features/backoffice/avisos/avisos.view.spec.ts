import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { AvisosView } from './avisos.view';
import { CasoAviso } from './avisos.gateway';
import { CASO, CASO_BAJO_MONTO, COLA, COLA_VACIA } from './avisos.testing';

describe('AvisosView', () => {
  const COLA_URL = '/web/operador/avisos?filtro=pendientes';
  const CASO_URL = `/web/operador/avisos/${CASO.id}`;

  function render(role: Role = 'operador') {
    TestBed.configureTestingModule({
      imports: [AvisosView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
      ],
    });
    const fixture = TestBed.createComponent(AvisosView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (id: string) => host.querySelector<HTMLElement>(`[data-testid="${id}"]`);
    return { fixture, http, host, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  function conCaso(caso: CasoAviso = CASO) {
    const r = render();
    r.http.expectOne(COLA_URL).flush(COLA);
    r.http.expectOne(CASO_URL).flush(caso);
    r.fixture.detectChanges();
    return r;
  }

  const PAGO = {
    clave_idempotencia: 'idem-111111111111',
    comprobante: 'CMP-AB12',
    monto: '420000.00',
    origen: 'operador',
    autorizado_por: 'camila.restrepo@solventa.co',
    pagado_en: '2026-11-02T12:00:00Z',
  };
  const APROBADO_BAJO_MONTO: CasoAviso = {
    ...CASO_BAJO_MONTO,
    estado: 'decidido',
    resultado: 'aprobado',
    estadoCola: 'aprobado',
    requiereRevision: false,
  };
  const PAGADO: CasoAviso = {
    ...APROBADO_BAJO_MONTO,
    estado: 'pagado',
    estadoCola: 'pagado',
    pago: PAGO,
    intentosPago: [
      {
        resultado: 'ejecutado',
        comprobante_devuelto: 'CMP-AB12',
        actor: 'camila',
        ocurrido_en: '2026-11-02T12:00:00Z',
      },
    ],
  };

  it('el asesor no ve la cola', () => {
    const { element } = render('asesor');
    expect(element('avisos')?.getAttribute('data-state')).toBe('no-permission');
  });

  it('cola vacía: chip Pendientes en cero, acción Actualizar y sin tabla ni detalle', () => {
    const { fixture, http, element } = render();
    http.expectOne(COLA_URL).flush(COLA_VACIA);
    fixture.detectChanges();

    expect(element('chip-pendientes')?.textContent).toContain('(0)');
    expect(element('avisos-actualizar')).not.toBeNull();
    expect(element('avisos-tabla')).toBeNull();
    expect(element('aviso-caso')).toBeNull();

    element('avisos-actualizar')!.click();
    http.expectOne(COLA_URL).flush(COLA_VACIA);
  });

  it('muestra evidencia, póliza y estado en una pantalla, sin editar la evidencia', () => {
    const { element } = conCaso();
    expect(element('aviso-SIN-2041')?.textContent).toContain('En revisión');
    const caso = element('aviso-caso')!;
    expect(caso.textContent).toContain('POL-88421');
    expect(caso.textContent).toContain('3.200.000');
    expect(element('aviso-motivo-revision')?.textContent).toContain('umbral');
    expect(element('aviso-evidencia')?.querySelector('a')?.getAttribute('href')).toBe(
      'https://s3/firmada',
    );
    expect(element('aviso-evidencia')?.querySelector('button, input')).toBeNull();
    // No es bajo monto: se ofrece enrutar a perito (HU-28).
    expect(element('aviso-perito')).not.toBeNull();
  });

  it('rechazar sin motivo deja el CTA deshabilitado y el aviso en revisión', () => {
    const { fixture, element } = conCaso();
    element('aviso-rechazar')!.click();
    fixture.detectChanges();

    const confirmar = element('confirm-dialog-confirmar') as HTMLButtonElement;
    expect(element('confirm-dialog')?.textContent).toContain('Rechazar aviso SIN-2041');
    expect(confirmar.disabled).toBeTrue();
    confirmar.click();
    fixture.detectChanges();
    expect(element('aviso-SIN-2041')?.textContent).toContain('En revisión');
  });

  it('rechazar con motivo envía la decisión al BFF', () => {
    const { fixture, http, element } = conCaso();
    element('aviso-rechazar')!.click();
    fixture.detectChanges();
    const motivo = element('confirm-dialog-motivo') as HTMLTextAreaElement;
    motivo.value = 'Falta soporte de la factura';
    motivo.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    element('confirm-dialog-confirmar')!.click();

    const req = http.expectOne('/web/operador/avisos/decision');
    expect(req.request.body).toEqual({
      siniestroId: CASO.id,
      decision: 'rechazar',
      motivo: 'Falta soporte de la factura',
    });
    req.flush({
      ...CASO,
      estado: 'decidido',
      resultado: 'rechazado',
      estadoCola: 'rechazado',
      requiereRevision: false,
    });
    http.expectOne(COLA_URL).flush(COLA_VACIA);
    fixture.detectChanges();
    expect(element('avisos-vacia')).not.toBeNull();
  });
  it('si falla la cola permite actualizar; los chips cambian de filtro', () => {
    const { fixture, http, host, element } = render();
    expect(element('avisos-loading')).not.toBeNull();
    http.expectOne(COLA_URL).flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('avisos-error')).not.toBeNull();

    (host.querySelector('[data-testid="avisos-error"] button') as HTMLButtonElement).click();
    http.expectOne(COLA_URL).flush(COLA_VACIA);
    fixture.detectChanges();
    expect(element('chip-rechazados')?.textContent).not.toContain('(');

    element('chip-rechazados')!.click();
    http
      .expectOne('/web/operador/avisos?filtro=rechazados')
      .flush({ ...COLA_VACIA, filtro: 'rechazados' });
    fixture.detectChanges();
    expect(element('chip-rechazados')?.getAttribute('aria-pressed')).toBe('true');
  });

  it('muestra cargando y error al abrir un caso', () => {
    const { fixture, http, element } = render();
    http.expectOne(COLA_URL).flush(COLA);
    fixture.detectChanges();
    expect(element('aviso-caso')?.getAttribute('data-state')).toBe('loading');
    http.expectOne(CASO_URL).flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('aviso-caso')?.getAttribute('data-state')).toBe('error');

    element('aviso-SIN-2041')!.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    http.expectOne(CASO_URL).flush(CASO);
    fixture.detectChanges();
    expect(element('aviso-SIN-2041')?.getAttribute('aria-selected')).toBe('true');

    element('aviso-SIN-2041')!.click();
    http.expectOne(CASO_URL).flush(CASO);
  });

  it('enruta a perito un caso que no es de bajo monto', () => {
    const { fixture, http, element } = conCaso();
    element('aviso-perito')!.click();
    fixture.detectChanges();
    expect((element('confirm-dialog-confirmar') as HTMLButtonElement).disabled).toBeFalse();
    element('confirm-dialog-confirmar')!.click();

    const req = http.expectOne(`/web/operador/avisos/${CASO.id}/perito`);
    expect(req.request.body).toEqual({ motivo: null });
    req.flush({ ...CASO, estado: 'enrutado', estadoCola: 'enrutado', requiereRevision: false });
    http.expectOne(COLA_URL).flush(COLA);
    fixture.detectChanges();
    // Ya no está en evaluación: sin acciones de decidir ni pagar.
    expect(element('aviso-aprobar')).toBeNull();
    expect(element('aviso-ir-pago')).toBeNull();
  });

  it('aprobar un bajo monto abre el pago; pagar una vez deja el comprobante', () => {
    const { fixture, http, element } = conCaso(CASO_BAJO_MONTO);
    expect(element('aviso-perito')).toBeNull();
    element('aviso-aprobar')!.click();
    fixture.detectChanges();
    element('confirm-dialog-confirmar')!.click();
    http.expectOne('/web/operador/avisos/decision').flush(APROBADO_BAJO_MONTO);
    http.expectOne(COLA_URL).flush(COLA);
    fixture.detectChanges();

    expect(element('avisos')?.getAttribute('data-modo')).toBe('pago');
    expect(element('pago-clave')?.textContent).toContain('idem-111111111111');
    expect(element('pago-monto')?.textContent).toContain('420.000');
    expect(element('pago-trazabilidad')?.textContent).toContain('Pendiente de desembolso');
    expect(element('pago-comprobante')).toBeNull();

    element('pago-confirmar')!.click();
    http
      .expectOne(`/web/operador/avisos/${CASO.id}/pago`)
      .flush({ pago: PAGO, reintento: false, caso: PAGADO });
    http.expectOne(COLA_URL).flush(COLA);
    fixture.detectChanges();
    const boton = element('pago-confirmar') as HTMLButtonElement;
    expect(boton.disabled).toBeTrue();
    expect(boton.textContent).toContain('Pago ya realizado');
    expect(element('pago-comprobante')?.textContent).toContain('CMP-AB12');
    expect(element('pago-reintento')).toBeNull();
    expect(element('pago-trazabilidad')?.textContent).toContain('Desembolso ejecutado');

    element('pago-volver')!.click();
    fixture.detectChanges();
    expect(element('avisos')?.getAttribute('data-modo')).toBe('cola');
  });

  it('en el pago informa el reintento idempotente y los errores', () => {
    const { fixture, http, element } = conCaso(APROBADO_BAJO_MONTO);
    element('aviso-ir-pago')!.click();
    fixture.detectChanges();
    expect(element('aviso-ir-pago')).toBeNull();

    element('pago-confirmar')!.click();
    http
      .expectOne(`/web/operador/avisos/${CASO.id}/pago`)
      .flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('pago-error')?.textContent).toContain('No se pudo completar');

    element('pago-confirmar')!.click();
    http
      .expectOne(`/web/operador/avisos/${CASO.id}/pago`)
      .flush(
        { mensaje: 'El monto supera el umbral automático' },
        { status: 422, statusText: 'Unprocessable' },
      );
    fixture.detectChanges();
    expect(element('pago-error')?.textContent).toContain('supera el umbral');

    element('pago-confirmar')!.click();
    http
      .expectOne(`/web/operador/avisos/${CASO.id}/pago`)
      .flush({ pago: PAGO, reintento: true, caso: PAGADO });
    http.expectOne(COLA_URL).flush(COLA);
    fixture.detectChanges();
    expect(element('pago-reintento')).not.toBeNull();

    element('pago-volver-aviso')!.click();
    fixture.detectChanges();
    expect(element('avisos')?.getAttribute('data-modo')).toBe('cola');
  });

  it('un caso ya pagado ofrece "Ver pago" con montos ausentes en cero', () => {
    const { fixture, element } = conCaso({
      ...PAGADO,
      montoEstimado: null,
      umbralAutomatico: null,
    });
    expect(element('aviso-ir-pago')?.textContent).toContain('Ver pago');
    element('aviso-ir-pago')!.click();
    fixture.detectChanges();
    expect(element('pago-monto')?.textContent).toContain('0');
    expect(element('pago-trazabilidad')?.textContent).not.toContain('Pendiente de desembolso');
  });

  it('muestra guiones, miniatura de imagen y la auditoría del operador', () => {
    const { element } = conCaso({
      ...CASO,
      fechaHecho: null,
      geo: null,
      montoEstimado: null,
      motivoRevision: null,
      evidencia: [
        { nombre: 'dano.png', tipo: 'foto', contentType: 'image/png', url: 'https://s3/foto' },
      ],
      decisiones: [
        ...CASO.decisiones,
        {
          origen: 'operador',
          actor: 'ana@solventa.co',
          resultado: 'enrutado',
          motivo: null,
          reglas: [],
          decidida_en: '2026-11-02T11:00:00Z',
        },
      ],
    });
    const caso = element('aviso-caso')!;
    expect(caso.textContent).toContain('Sin geoetiqueta');
    expect(caso.textContent).toContain('—');
    expect(element('aviso-motivo-revision')).toBeNull();
    expect(element('aviso-evidencia')?.querySelector('img')?.getAttribute('alt')).toBe('dano.png');
    const auditoria = element('aviso-auditoria')!.textContent!;
    expect(auditoria).toContain('Motor de reglas');
    expect(auditoria).toContain('ana@solventa.co');
  });

  it('muestra el rechazo del núcleo y el error técnico en el caso', () => {
    const { fixture, http, element } = conCaso();
    element('aviso-aprobar')!.click();
    fixture.detectChanges();
    element('confirm-dialog-confirmar')!.click();
    http
      .expectOne('/web/operador/avisos/decision')
      .flush({ mensaje: 'El caso ya fue decidido' }, { status: 409, statusText: 'Conflict' });
    fixture.detectChanges();
    expect(element('aviso-accion-error')?.textContent).toContain('ya fue decidido');

    element('aviso-aprobar')!.click();
    fixture.detectChanges();
    element('confirm-dialog-cancelar')!.click();
    fixture.detectChanges();
    expect(element('confirm-dialog')).toBeNull();

    element('aviso-aprobar')!.click();
    fixture.detectChanges();
    element('confirm-dialog-confirmar')!.click();
    http
      .expectOne('/web/operador/avisos/decision')
      .flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('aviso-accion-error')?.textContent).toContain('No se pudo completar');
  });
});
