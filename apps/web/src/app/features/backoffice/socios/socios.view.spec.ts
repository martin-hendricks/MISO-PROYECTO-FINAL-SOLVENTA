import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { ACTIVO_ID, CREADO, REVOCADO_ID, SOCIOS, VIGENTE_ID } from './socios.testing';
import { SociosView } from './socios.view';

const URL = '/web/backoffice/socios';

describe('SociosView', () => {
  function render(role: Role) {
    TestBed.configureTestingModule({
      imports: [SociosView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
      ],
    });
    const fixture = TestBed.createComponent(SociosView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  function listado(role: Role) {
    const rendered = render(role);
    rendered.http
      .expectOne((candidate) => candidate.method === 'GET' && candidate.url === URL)
      .flush({ socios: SOCIOS });
    rendered.fixture.detectChanges();
    return rendered;
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  for (const role of ['asesor', 'operador'] as const) {
    it(`lists the partners and their credentials for the ${role}`, () => {
      const { element } = listado(role);

      expect(element('section-socios')?.getAttribute('data-state')).toBe('ready');
      expect(element(`socio-${ACTIVO_ID}`)?.textContent).toContain('Aliado local');
      expect(element(`socio-${ACTIVO_ID}`)?.textContent).toContain('catalogo:leer');
      expect(element(`credencial-${VIGENTE_ID}`)?.textContent).toContain('Vigente');
      expect(element(`rotar-${ACTIVO_ID}`)).not.toBeNull();
      expect(element(`revocar-credencial-${VIGENTE_ID}`)).not.toBeNull();
      expect(element('socios-new')).not.toBeNull();
    });
  }

  it('keeps a customer out of the partners', () => {
    const { http, element } = render('cliente');

    http.expectNone(URL);
    expect(element('section-socios')?.getAttribute('data-state')).toBe('no-permission');
    expect(element('no-permission')).not.toBeNull();
  });

  it('shows no actions for a revoked partner', () => {
    const { element, host } = listado('operador');
    const fila = element(`socio-${REVOCADO_ID}`)!;

    expect(fila.textContent).toContain('Revocado');
    expect(element(`rotar-${REVOCADO_ID}`)).toBeNull();
    expect(element(`revocar-${REVOCADO_ID}`)).toBeNull();
    expect(host.querySelectorAll(`[data-testid^="revocar-credencial-"]`).length).toBe(1);
  });

  it('creates a partner, shows its key once and hides it on dismiss', () => {
    const { fixture, http, element } = listado('asesor');

    element('socios-new')!.click();
    fixture.detectChanges();
    expect((element('socios-save') as HTMLButtonElement).disabled).toBeTrue();
    const nombre = element('socios-nombre') as HTMLInputElement;
    expect(nombre.getAttribute('aria-required')).toBe('true');
    nombre.value = 'Nuevo aliado';
    nombre.dispatchEvent(new Event('input'));
    (element('socios-alcance-catalogo:leer') as HTMLInputElement).click();
    fixture.detectChanges();
    element('socios-form')!.dispatchEvent(new Event('submit'));

    const alta = http.expectOne(
      (candidate) => candidate.method === 'POST' && candidate.url === URL,
    );
    expect(alta.request.body).toEqual({ nombre: 'Nuevo aliado', alcances: ['catalogo:leer'] });
    alta.flush(
      { codigo: 'SOCIO_DUPLICADO', mensaje: 'Ya existe' },
      { status: 409, statusText: 'Conflict' },
    );
    fixture.detectChanges();
    expect(element('socios-mensaje')?.textContent).toContain('Ya existe');

    element('socios-form')!.dispatchEvent(new Event('submit'));
    http
      .expectOne((candidate) => candidate.method === 'POST')
      .flush(CREADO, { status: 201, statusText: 'Created' });
    http.expectOne((candidate) => candidate.method === 'GET').flush({ socios: SOCIOS });
    fixture.detectChanges();

    expect(element('socios-form')).toBeNull();
    expect(element('socios-clave')?.textContent).toContain(CREADO.apiKey);
    expect(element('socios-copiar')).not.toBeNull();

    element('socios-clave-cerrar')!.click();
    fixture.detectChanges();
    expect(element('socios-clave')).toBeNull();
  });

  it('rotates a key and shows the new one', () => {
    const { fixture, http, element } = listado('operador');

    element(`rotar-${ACTIVO_ID}`)!.click();
    http
      .expectOne(`${URL}/${ACTIVO_ID}/credenciales`)
      .flush(
        { credencialId: 'nueva', apiKey: 'sk_rotada_456' },
        { status: 201, statusText: 'Created' },
      );
    http.expectOne((candidate) => candidate.method === 'GET').flush({ socios: SOCIOS });
    fixture.detectChanges();

    expect(element('socios-clave')?.textContent).toContain('sk_rotada_456');
  });

  it('revokes a credential and a partner after confirming', () => {
    const { fixture, http, element } = listado('operador');

    element(`revocar-credencial-${VIGENTE_ID}`)!.click();
    fixture.detectChanges();
    element('confirm-dialog-confirmar')!.click();
    http
      .expectOne(`${URL}/${ACTIVO_ID}/credenciales/${VIGENTE_ID}`)
      .flush(null, { status: 204, statusText: 'No Content' });
    http.expectOne((candidate) => candidate.method === 'GET').flush({ socios: SOCIOS });
    fixture.detectChanges();

    element(`revocar-${ACTIVO_ID}`)!.click();
    fixture.detectChanges();
    element('confirm-dialog-confirmar')!.click();
    http.expectOne(`${URL}/${ACTIVO_ID}/revocacion`).flush({ ...SOCIOS[0], estado: 'revocado' });
    http.expectOne((candidate) => candidate.method === 'GET').flush({ socios: SOCIOS });
    fixture.detectChanges();

    expect(element('confirm-dialog')).toBeNull();
  });

  it('shows the empty state and retries after an error', () => {
    const { fixture, http, element } = render('asesor');
    http.expectOne(URL).error(new ProgressEvent('error'));
    fixture.detectChanges();
    expect(element('socios-error')).not.toBeNull();

    element('socios-retry')!.click();
    http.expectOne(URL).flush({ socios: [] });
    fixture.detectChanges();

    expect(element('socios-empty')).not.toBeNull();
  });

  it('closes the create form and the confirmation without writing', () => {
    const { fixture, element } = listado('asesor');

    element('socios-new')!.click();
    fixture.detectChanges();
    element('socios-cancel')!.click();
    fixture.detectChanges();
    expect(element('socios-form')).toBeNull();

    element(`revocar-${ACTIVO_ID}`)!.click();
    fixture.detectChanges();
    element('confirm-dialog-cancelar')!.click();
    fixture.detectChanges();
    expect(element('confirm-dialog')).toBeNull();
  });

  async function claveRotada() {
    const rendered = listado('operador');
    rendered.element(`rotar-${ACTIVO_ID}`)!.click();
    rendered.http
      .expectOne(`${URL}/${ACTIVO_ID}/credenciales`)
      .flush({ credencialId: 'nueva', apiKey: 'sk_rotada_456' });
    rendered.http.expectOne((candidate) => candidate.method === 'GET').flush({ socios: SOCIOS });
    rendered.fixture.detectChanges();
    return rendered;
  }

  it('copies the key to the clipboard', async () => {
    const writeText = jasmine.createSpy('writeText').and.resolveTo();
    spyOnProperty(navigator, 'clipboard', 'get').and.returnValue({
      writeText,
    } as unknown as Clipboard);
    const { fixture, element } = await claveRotada();

    element('socios-copiar')!.click();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(writeText).toHaveBeenCalledWith('sk_rotada_456');
    expect(element('socios-copiar')?.textContent).toContain('Copiada');
    expect(element('socios-copiado')?.getAttribute('role')).toBe('status');
    expect(element('socios-copiado')?.textContent?.trim()).toBe('Copiada');
  });

  it('keeps the copy label when the clipboard refuses', async () => {
    const writeText = jasmine.createSpy('writeText').and.rejectWith(new Error('denegado'));
    spyOnProperty(navigator, 'clipboard', 'get').and.returnValue({
      writeText,
    } as unknown as Clipboard);
    const { fixture, element } = await claveRotada();

    element('socios-copiar')!.click();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(element('socios-copiar')?.textContent).toContain('Copiar');
    expect(element('socios-copiado')?.textContent?.trim()).toBe('');
  });

  it('does nothing when there is no clipboard', async () => {
    spyOnProperty(navigator, 'clipboard', 'get').and.returnValue(undefined as unknown as Clipboard);
    const { fixture, element } = await claveRotada();

    element('socios-copiar')!.click();
    fixture.detectChanges();

    expect(element('socios-clave')?.textContent).toContain('sk_rotada_456');
  });
});
