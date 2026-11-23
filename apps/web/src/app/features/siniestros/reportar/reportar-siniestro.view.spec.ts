import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { POLIZAS } from '../../polizas/polizas.testing';
import { hoyLocal, ReportarSiniestroView, ubicacionDelNavegador } from './reportar-siniestro.view';

describe('ReportarSiniestroView', () => {
  const POLIZAS_URL = '/web/cliente/polizas';
  const AVISO_URL = '/web/cliente/siniestros';
  const PNG = new File(['png'], 'dano.png', { type: 'image/png' });

  function render() {
    TestBed.configureTestingModule({
      imports: [ReportarSiniestroView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
      ],
    });
    const fixture = TestBed.createComponent(ReportarSiniestroView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = <T extends HTMLElement = HTMLElement>(id: string) =>
      host.querySelector<T>(`[data-testid="${id}"]`);
    const escribir = (id: string, valor: string, evento = 'input') => {
      const campo = element<HTMLInputElement>(id)!;
      campo.value = valor;
      campo.dispatchEvent(new Event(evento));
      fixture.detectChanges();
    };
    return { fixture, http, host, element, escribir };
  }

  function elegirArchivo(input: HTMLInputElement, archivo: File | null) {
    const transfer = new DataTransfer();
    if (archivo) {
      transfer.items.add(archivo);
    }
    input.files = transfer.files;
    input.dispatchEvent(new Event('change'));
  }

  /** Formulario completo con la única póliza vigente preseleccionada. */
  function hastaEvidencia() {
    const r = render();
    r.http.expectOne(POLIZAS_URL).flush({ polizas: POLIZAS });
    r.fixture.detectChanges();
    r.escribir('aviso-fecha', '2026-11-01');
    r.escribir('aviso-descripcion', 'Pantalla rota');
    r.element('aviso-continuar')!.click();
    r.fixture.detectChanges();
    return r;
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('muestra cargando y luego el formulario con la póliza vigente y el ramo en el título', () => {
    const { fixture, http, host, element } = render();
    expect(host.textContent).toContain('Cargando tus pólizas');

    http.expectOne(POLIZAS_URL).flush({ polizas: POLIZAS });
    fixture.detectChanges();

    const opciones = element<HTMLSelectElement>('aviso-poliza')!.options;
    expect(opciones.length).toBe(2); // "Elige una póliza" + la vigente
    expect(host.querySelector('h1')?.textContent).toContain('Hogar');
  });

  it('sin pólizas vigentes muestra el estado vacío', () => {
    const { fixture, http, element } = render();
    http.expectOne(POLIZAS_URL).flush({ polizas: [POLIZAS[1]] });
    fixture.detectChanges();
    expect(element('reportar-sin-polizas')).not.toBeNull();
  });

  it('si falla la carga de pólizas permite reintentar', () => {
    const { fixture, http, host, element } = render();
    http.expectOne(POLIZAS_URL).flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('reportar-polizas-error')).not.toBeNull();

    (
      host.querySelector('[data-testid="reportar-polizas-error"] button') as HTMLButtonElement
    ).click();
    http.expectOne(POLIZAS_URL).flush({ polizas: POLIZAS });
    fixture.detectChanges();
    expect(element('aviso-poliza')).not.toBeNull();
  });

  it('marca los campos inválidos y no avanza a evidencia', () => {
    const { fixture, http, host, element, escribir } = render();
    http
      .expectOne(POLIZAS_URL)
      .flush({ polizas: [POLIZAS[0], { ...POLIZAS[0], numero: 'POL-2' }] });
    fixture.detectChanges();
    expect(host.querySelector('h1')?.textContent).not.toContain('·'); // sin póliza elegida aún

    element('aviso-continuar')!.click();
    fixture.detectChanges();
    // Un mensaje por campo, sin resumen genérico, y cada campo lo referencia.
    expect(element('aviso-errores')).toBeNull();
    expect(element('aviso-poliza-error')).not.toBeNull();
    expect(element('aviso-fecha-error')).not.toBeNull();
    expect(element('aviso-descripcion-error')).not.toBeNull();
    expect(element('aviso-poliza')?.getAttribute('aria-describedby')).toBe('aviso-poliza-error');
    expect(element('aviso-fecha')?.getAttribute('aria-describedby')).toBe('aviso-fecha-error');
    expect(element('aviso-descripcion')?.getAttribute('aria-describedby')).toBe(
      'aviso-descripcion-error',
    );
    expect(element('aviso-poliza')?.getAttribute('aria-invalid')).toBe('true');

    escribir('aviso-poliza', 'POL-2', 'change');
    escribir('aviso-fecha', '2026-11-01');
    expect(element('aviso-poliza-error')).toBeNull();
    expect(element('aviso-fecha-error')).toBeNull();
    expect(element('aviso-poliza')?.getAttribute('aria-describedby')).toBeNull();
    expect(element('aviso-fecha')?.getAttribute('aria-describedby')).toBeNull();
    expect(element('aviso-descripcion-error')).not.toBeNull();
    expect(element('aviso-descripcion')?.getAttribute('aria-describedby')).toBe(
      'aviso-descripcion-error',
    );
    expect(element('aviso-poliza')?.getAttribute('aria-invalid')).toBe('false');
    expect(element('reportar-siniestro')?.getAttribute('data-paso')).toBe('formulario');

    escribir('aviso-descripcion', 'Pantalla rota');
    expect(element('aviso-descripcion-error')).toBeNull();
    expect(element('aviso-descripcion')?.getAttribute('aria-describedby')).toBeNull();
  });

  it('valida el archivo, permite volver y guarda la ubicación del navegador', async () => {
    const { fixture, element } = hastaEvidencia();
    expect(element('reportar-siniestro')?.getAttribute('data-paso')).toBe('evidencia');
    expect((element('evidencia-enviar') as HTMLButtonElement).disabled).toBeTrue();
    expect(element('evidencia-ubicacion')?.textContent).toContain('pendiente');

    elegirArchivo(
      element<HTMLInputElement>('evidencia-input')!,
      new File(['x'], 'a.exe', { type: 'application/x-msdownload' }),
    );
    fixture.detectChanges();
    expect(element('evidencia-error')?.textContent).toContain('PNG, JPG o PDF');

    elegirArchivo(element<HTMLInputElement>('evidencia-input')!, null);
    elegirArchivo(element<HTMLInputElement>('evidencia-input')!, PNG);
    fixture.detectChanges();
    expect(element('evidencia-archivo')?.textContent).toContain('dano.png');

    spyOn(navigator.geolocation, 'getCurrentPosition').and.callFake((ok: PositionCallback) =>
      ok({
        coords: { latitude: 4.6533, longitude: -74.0836, accuracy: 12.4 },
      } as GeolocationPosition),
    );
    element('evidencia-usar-ubicacion')!.click();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(element('evidencia-ubicacion')?.getAttribute('data-state')).toBe('guardada');
    expect(element('evidencia-usar-ubicacion')).toBeNull();

    element('evidencia-volver')!.click();
    fixture.detectChanges();
    expect(element('reportar-siniestro')?.getAttribute('data-paso')).toBe('formulario');
  });

  it('acepta el archivo arrastrado y soltado', () => {
    const { fixture, element } = hastaEvidencia();
    const zona = element('evidencia-dropzone')!;

    zona.dispatchEvent(new DragEvent('dragover', { cancelable: true }));
    fixture.detectChanges();
    expect(zona.classList).toContain('arrastrando');
    zona.dispatchEvent(new DragEvent('dragleave'));
    fixture.detectChanges();
    expect(zona.classList).not.toContain('arrastrando');

    zona.dispatchEvent(new DragEvent('drop', { cancelable: true })); // sin archivos
    const transfer = new DataTransfer();
    transfer.items.add(PNG);
    zona.dispatchEvent(new DragEvent('drop', { cancelable: true, dataTransfer: transfer }));
    fixture.detectChanges();
    expect(element('evidencia-archivo')?.textContent).toContain('dano.png');
  });

  it('envía el aviso y muestra "Aviso recibido" con el id y los dos CTA', () => {
    const { fixture, http, element } = hastaEvidencia();
    elegirArchivo(element<HTMLInputElement>('evidencia-input')!, PNG);
    fixture.detectChanges();

    element('evidencia-enviar')!.click();
    fixture.detectChanges();
    expect(element('evidencia-enviar')?.textContent).toContain('Enviando');
    const req = http.expectOne(AVISO_URL);
    expect(req.request.headers.has('Idempotency-Key')).toBeTrue();
    req.flush({ id: 'id-1', siniestroId: 'SIN-1001', estado: 'recibido' });
    fixture.detectChanges();

    expect(element('aviso-recibido-id')?.textContent).toContain('SIN-1001');
    expect(element('aviso-recibido-mis-siniestros')?.getAttribute('href')).toBe('/siniestros');
    expect(element('aviso-recibido-inicio')?.getAttribute('href')).toBe('/inicio');
  });

  it('muestra el error de red y el rechazo del núcleo', () => {
    const { fixture, http, element } = hastaEvidencia();
    elegirArchivo(element<HTMLInputElement>('evidencia-input')!, PNG);
    fixture.detectChanges();

    element('evidencia-enviar')!.click();
    http.expectOne(AVISO_URL).flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('evidencia-envio-error')).not.toBeNull();

    element('evidencia-enviar')!.click();
    http
      .expectOne(AVISO_URL)
      .flush(
        { codigo: 'evidencia_vacia', mensaje: 'El archivo está vacío' },
        { status: 422, statusText: 'Unprocessable' },
      );
    fixture.detectChanges();
    expect(element('evidencia-rechazo')?.textContent).toContain('El archivo está vacío');
  });
});

describe('ubicacionDelNavegador', () => {
  it('rechaza si el navegador no tiene geolocalización', async () => {
    await expectAsync(ubicacionDelNavegador(null)).toBeRejected();
  });

  it('rechaza si el usuario bloquea el permiso', async () => {
    const geo = {
      getCurrentPosition: (_ok: PositionCallback, error: PositionErrorCallback) =>
        error({ code: 1 } as GeolocationPositionError),
    } as Geolocation;
    await expectAsync(ubicacionDelNavegador(geo)).toBeRejected();
  });

  it('redondea la precisión en metros', async () => {
    const geo = {
      getCurrentPosition: (ok: PositionCallback) =>
        ok({ coords: { latitude: 1, longitude: 2, accuracy: 9.6 } } as GeolocationPosition),
    } as Geolocation;
    await expectAsync(ubicacionDelNavegador(geo)).toBeResolvedTo({
      lat: 1,
      lng: 2,
      precisionM: 10,
    });
  });
});

describe('hoyLocal', () => {
  it('devuelve la fecha local en formato ISO', () => {
    expect(hoyLocal()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
