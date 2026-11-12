import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { ConsentimientoPerfilView } from './consentimiento-perfil.view';

describe('ConsentimientoPerfilView', () => {
  const URL = '/web/cliente/consentimiento-perfil';

  function render(estado: object = { estado: 'vigente', otorgadoEn: '2026-10-01T10:00:00Z' }) {
    TestBed.configureTestingModule({
      imports: [ConsentimientoPerfilView],
      providers: [provideHttpClient(), provideHttpClientTesting(), ...provideSolventaI18n()],
    });
    const fixture = TestBed.createComponent(ConsentimientoPerfilView);
    fixture.detectChanges();
    const http = TestBed.inject(HttpTestingController);
    const carga = http.expectOne(URL);
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

  it('shows the profiling consent row with when it was granted', () => {
    const { q } = render();

    expect(q('perfil-consentimiento-open')?.textContent).toContain(
      'Perfilamiento para vida hipotecario',
    );
    expect(q('perfil-consentimiento-auditoria')?.textContent).toContain('Otorgado');
    expect(q('confirm-dialog')).toBeNull();
  });

  it('shows no row when the customer never granted the profiling consent', () => {
    const { q } = render({ estado: 'sin_consentimiento' });

    expect(q('perfil-consentimiento')).toBeNull();
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

  it('revokes through the BFF and shows the revocation in the row', () => {
    const { http, q, click, fixture } = render();

    click('perfil-consentimiento-open');
    click('confirm-dialog-confirmar');
    const revocacion = http.expectOne(URL);
    expect(revocacion.request.method).toBe('DELETE');
    revocacion.flush({ estado: 'revocado', revocadoEn: '2026-11-11T15:30:00Z' });
    fixture.detectChanges();

    expect(q('confirm-dialog')).toBeNull();
    expect(q('perfil-consentimiento-auditoria')?.textContent).toContain('Revocado');
    expect((q('perfil-consentimiento-open') as HTMLButtonElement).disabled).toBeTrue();
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
});
