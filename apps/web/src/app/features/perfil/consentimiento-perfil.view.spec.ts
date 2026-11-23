import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { TipoConsentimiento } from './consentimiento-perfil.gateway';
import { ConsentimientoPerfilView } from './consentimiento-perfil.view';

describe('ConsentimientoPerfilView', () => {
  const URL = '/web/cliente/consentimiento-perfil';
  const URL_DATOS = '/web/cliente/consentimiento';

  function render(
    estado: object = { estado: 'vigente', otorgadoEn: '2026-10-01T10:00:00Z' },
    tipo: TipoConsentimiento = 'perfil',
  ) {
    TestBed.configureTestingModule({
      imports: [ConsentimientoPerfilView],
      providers: [provideHttpClient(), provideHttpClientTesting(), ...provideSolventaI18n()],
    });
    const fixture = TestBed.createComponent(ConsentimientoPerfilView);
    fixture.componentRef.setInput('tipo', tipo);
    fixture.detectChanges();
    const http = TestBed.inject(HttpTestingController);
    const carga = http.expectOne(tipo === 'datos' ? URL_DATOS : URL);
    expect(carga.request.method).toBe('GET');
    carga.flush(estado);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const q = (id: string) => host.querySelector(`[data-testid="${id}"]`) as HTMLElement | null;
    const click = (id: string) => {
      q(id)!.click();
      fixture.detectChanges();
    };
    return { fixture, http, q, click };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('shows the Vida Crediticia consent row with when it was granted', () => {
    const { q } = render();

    expect(q('perfil-consentimiento-open')?.textContent).toContain(
      'Consentimiento Vida Crediticia',
    );
    expect(q('perfil-consentimiento-auditoria')?.textContent).toContain('Otorgado');
    expect(q('confirm-dialog')).toBeNull();
  });

  it('shows the row without an active originación when there is no profiling consent', () => {
    const { q, click } = render({ estado: 'sin_consentimiento' });

    expect(q('perfil-consentimiento-auditoria')?.textContent?.trim()).toBe(
      'Sin originación activa',
    );

    click('perfil-consentimiento-open');

    expect(q('confirm-dialog')).toBeNull();
    expect(q('perfil-dialog')?.textContent).toContain('Vida Crediticia');
    click('perfil-dialog-entendido');
    expect(q('perfil-dialog')).toBeNull();
  });

  it('explains what revoking does before asking to confirm', () => {
    const { q, click } = render();

    click('perfil-consentimiento-open');

    expect(q('confirm-dialog')?.textContent).toContain('Open Finance y Open Data');
    expect(q('confirm-dialog-confirmar')?.textContent).toContain('Revocar');
  });

  it('cancelling the dialog does not call the BFF', () => {
    const { q, click } = render();

    click('perfil-consentimiento-open');
    click('confirm-dialog-cancelar');

    expect(q('confirm-dialog')).toBeNull();
    expect(q('perfil-consentimiento-auditoria')?.textContent).toContain('Otorgado');
  });

  it('revokes through the BFF and then only informs on the row', () => {
    const { http, q, click, fixture } = render();

    click('perfil-consentimiento-open');
    click('confirm-dialog-confirmar');
    const revocacion = http.expectOne(URL);
    expect(revocacion.request.method).toBe('DELETE');
    revocacion.flush({ estado: 'revocado', revocadoEn: '2026-11-11T15:30:00Z' });
    fixture.detectChanges();

    expect(q('confirm-dialog')).toBeNull();
    expect(q('perfil-consentimiento-auditoria')?.textContent).toContain('Revocado');

    click('perfil-consentimiento-open');
    expect(q('confirm-dialog')).toBeNull();
    expect(q('perfil-dialog')).not.toBeNull();
  });

  it('tells the customer when the revocation failed', () => {
    const { http, q, click, fixture } = render();

    click('perfil-consentimiento-open');
    click('confirm-dialog-confirmar');
    http.expectOne(URL).flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();

    expect(q('perfil-consentimiento-error')?.getAttribute('role')).toBe('alert');
    expect(q('perfil-consentimiento-auditoria')?.textContent).toContain('Otorgado');
  });

  it('gives the focus back to the open button when a dialog closes', () => {
    const { fixture, q, click } = render();
    document.body.appendChild(fixture.nativeElement);
    const abrir = q('perfil-consentimiento-open') as HTMLButtonElement;
    abrir.focus();

    click('perfil-consentimiento-open');
    click('confirm-dialog-cancelar');

    expect(document.activeElement).toBe(abrir);
    (fixture.nativeElement as HTMLElement).remove();
  });

  it('manages the data consent through its own BFF route', () => {
    const { http, q, click, fixture } = render(
      { estado: 'vigente', otorgadoEn: '2026-10-01T10:00:00Z' },
      'datos',
    );

    expect(q('perfil-datos-open')?.textContent).toContain('Consentimiento de datos');
    expect(q('perfil-datos-auditoria')?.textContent).toContain('Otorgado');

    click('perfil-datos-open');
    expect(q('confirm-dialog')?.textContent).toContain('habeas data');
    click('confirm-dialog-confirmar');
    const revocacion = http.expectOne(URL_DATOS);
    expect(revocacion.request.method).toBe('DELETE');
    revocacion.flush({ estado: 'revocado', revocadoEn: '2026-11-22T15:30:00Z' });
    fixture.detectChanges();

    expect(q('perfil-datos-auditoria')?.textContent).toContain('Revocado');
  });

  it('shows the data consent as not in force when the core has none', () => {
    const { q } = render({ estado: 'sin_consentimiento' }, 'datos');

    expect(q('perfil-datos-auditoria')?.textContent?.trim()).toBe('Sin consentimiento vigente');
  });

  it('shows no audit line when the consent cannot be read', () => {
    TestBed.configureTestingModule({
      imports: [ConsentimientoPerfilView],
      providers: [provideHttpClient(), provideHttpClientTesting(), ...provideSolventaI18n()],
    });
    const fixture = TestBed.createComponent(ConsentimientoPerfilView);
    fixture.componentRef.setInput('tipo', 'datos');
    fixture.detectChanges();
    TestBed.inject(HttpTestingController)
      .expectOne(URL_DATOS)
      .flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();

    const host = fixture.nativeElement as HTMLElement;
    expect(host.querySelector('[data-testid="perfil-datos-auditoria"]')?.textContent?.trim()).toBe(
      '',
    );
  });
});
