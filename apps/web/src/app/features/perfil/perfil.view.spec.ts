import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { LocaleService } from '../../core/i18n/locale.service';
import { SessionService } from '../../core/session/session.service';
import { PerfilView } from './perfil.view';

describe('PerfilView', () => {
  const PERFIL = {
    usuarioId: '11111111-1111-1111-1111-111111111111',
    correo: 'camila@correo.com',
    nombre: 'Camila',
    apellidos: 'Restrepo',
    tipoDocumento: 'CC',
    documento: '1023456789',
  };

  function render(perfil: object | null = PERFIL) {
    const signOut = jasmine.createSpy('signOut');
    TestBed.configureTestingModule({
      imports: [PerfilView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        { provide: SessionService, useValue: { signOut } },
      ],
    });
    TestBed.inject(LocaleService).use('es-CO');
    const fixture = TestBed.createComponent(PerfilView);
    fixture.detectChanges();
    const http = TestBed.inject(HttpTestingController);
    const carga = http.expectOne('/web/cliente/perfil');
    if (perfil) {
      carga.flush(perfil);
    } else {
      carga.flush({}, { status: 503, statusText: 'Unavailable' });
    }
    http.expectOne('/web/cliente/consentimiento').flush({
      estado: 'vigente',
      otorgadoEn: '2026-10-01T10:00:00Z',
    });
    http.expectOne('/web/cliente/consentimiento-perfil').flush({ estado: 'sin_consentimiento' });
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const q = (id: string) => host.querySelector(`[data-testid="${id}"]`) as HTMLElement | null;
    const click = (id: string) => {
      q(id)!.click();
      fixture.detectChanges();
    };
    return { fixture, http, host, q, click, signOut };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('shows the identity with name and document, without KYC editing', () => {
    const { host, q } = render();

    expect(host.querySelector('h1')?.textContent).toContain('Perfil');
    expect(q('perfil-nombre')?.textContent?.trim()).toBe('Camila Restrepo · CC 1.023.456.789');
    expect(host.querySelector('input')).toBeNull();
  });

  it('hides the identity line when the profile cannot be read', () => {
    const { q } = render(null);

    expect(q('perfil-nombre')).toBeNull();
    expect(q('perfil-idioma-region-open')).not.toBeNull();
  });

  it('shows a non numeric document as it comes', () => {
    const { q } = render({ ...PERFIL, tipoDocumento: '', documento: 'X-12' });

    expect(q('perfil-nombre')?.textContent?.trim()).toBe('Camila Restrepo · X-12');
  });

  it('lists the hub rows of the design', () => {
    const { q } = render();

    expect(q('perfil-idioma-region-open')?.textContent).toContain('Idioma y región');
    expect(q('perfil-idioma-resumen')?.textContent?.trim()).toBe(
      'Español · Colombia · es-CO · COP',
    );
    expect(q('perfil-datos-open')?.textContent).toContain('Consentimiento de datos');
    expect(q('perfil-consentimiento-open')?.textContent).toContain(
      'Consentimiento Vida Crediticia',
    );
    expect(q('perfil-consentimiento-auditoria')?.textContent).toContain('Sin originación activa');
    expect(q('perfil-dispositivo')?.textContent).toContain('app Android');
  });

  it('does not offer Renovar, Modificar or Cancelar', () => {
    const { host } = render();

    const texto = host.textContent ?? '';
    expect(texto).not.toContain('Renovar');
    expect(texto).not.toContain('Modificar');
    expect(texto).not.toContain('Cancelar');
  });

  it('opens idioma y región in a dialog closed with Listo', () => {
    const { q, click } = render();

    expect(q('idioma-region')).toBeNull();
    click('perfil-idioma-region-open');

    expect(q('perfil-dialog')?.getAttribute('role')).toBe('dialog');
    expect(q('idioma-region-done')?.textContent).toContain('Listo');

    click('idioma-region-es-MX');
    expect(q('perfil-idioma-resumen')?.textContent?.trim()).toBe('Español · México · es-MX · MXN');

    click('idioma-region-done');
    expect(q('perfil-dialog')).toBeNull();
  });

  it('closes the idioma y región dialog with Escape', () => {
    const { fixture, q, click } = render();

    click('perfil-idioma-region-open');
    q('perfil-dialog')!.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }),
    );
    fixture.detectChanges();

    expect(q('perfil-dialog')).toBeNull();
  });

  it('asks to confirm before signing out', () => {
    const { q, click, signOut } = render();

    click('perfil-cerrar-sesion');

    expect(q('confirm-dialog')?.textContent).toContain('Cerrar sesión');
    click('confirm-dialog-cancelar');
    expect(q('confirm-dialog')).toBeNull();
    expect(signOut).not.toHaveBeenCalled();
  });

  it('signs out and goes back to login once confirmed', () => {
    const { click, signOut } = render();
    const navegar = spyOn(TestBed.inject(Router), 'navigateByUrl').and.resolveTo(true);

    click('perfil-cerrar-sesion');
    click('confirm-dialog-confirmar');

    expect(signOut).toHaveBeenCalledTimes(1);
    expect(navegar).toHaveBeenCalledOnceWith('/login');
  });
});
