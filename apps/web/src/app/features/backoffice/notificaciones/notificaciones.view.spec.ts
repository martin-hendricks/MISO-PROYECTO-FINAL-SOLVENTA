import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { NotificacionesView } from './notificaciones.view';
import { AUDIENCIA, HISTORIAL, RESULTADO } from './notificaciones.testing';

describe('NotificacionesView', () => {
  function render(role: Role) {
    TestBed.configureTestingModule({
      imports: [NotificacionesView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
      ],
    });
    const fixture = TestBed.createComponent(NotificacionesView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) => host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, element };
  }

  function listo() {
    const rendered = render('operador');
    rendered.http.expectOne('/web/operador/notificaciones/audiencia').flush({ usuarios: AUDIENCIA });
    rendered.http.expectOne('/web/operador/notificaciones/difusiones').flush({ items: HISTORIAL });
    rendered.fixture.detectChanges();
    return rendered;
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('keeps the advisor out before calling the BFF', () => {
    const { http, element } = render('asesor');
    http.expectNone('/web/operador/notificaciones/audiencia');
    expect(element('section-notificaciones')?.getAttribute('data-state')).toBe('no-permission');
    expect(element('no-permission')?.getAttribute('data-required')).toBe('operador');
  });

  it('updates the remaining counts, the preview and the send result', () => {
    const { fixture, http, element } = listo();
    const titulo = element('notificaciones-titulo') as HTMLInputElement;
    const cuerpo = element('notificaciones-cuerpo') as HTMLTextAreaElement;

    expect((element('notificaciones-enviar') as HTMLButtonElement).disabled).toBeTrue();
    expect(element('notificaciones-restante-titulo')?.textContent).toBe('80');

    titulo.value = 'Aviso';
    titulo.dispatchEvent(new Event('input'));
    cuerpo.value = 'Texto del operador';
    cuerpo.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect(element('notificaciones-restante-titulo')?.textContent).toBe(String(80 - 'Aviso'.length));
    expect(element('notificaciones-preview-titulo')?.textContent).toBe('Aviso');
    expect(element('notificaciones-preview-cuerpo')?.textContent).toBe('Texto del operador');
    expect((element('notificaciones-enviar') as HTMLButtonElement).disabled).toBeFalse();

    const form = element('notificaciones-form');
    const audiencia = form?.querySelector('fieldset');
    const tituloCampo = element('notificaciones-titulo');
    expect(audiencia).not.toBeNull();
    expect(
      Boolean(
        audiencia &&
          tituloCampo &&
          audiencia.compareDocumentPosition(tituloCampo) & Node.DOCUMENT_POSITION_FOLLOWING,
      ),
    ).toBeTrue();

    (element('notificaciones-audiencia-elegidos') as HTMLInputElement).dispatchEvent(new Event('change'));
    fixture.detectChanges();
    expect(element('notificaciones-audiencia')?.textContent).toContain('Ana Ruiz');
    expect(element('notificaciones-audiencia')?.textContent).toContain('1020334556');
    expect(element('notificaciones-audiencia')?.textContent).toContain('Luis Paz');
    expect(element('notificaciones-audiencia')?.textContent).toContain('52448901');
    (element('notificaciones-audiencia-todos') as HTMLInputElement).dispatchEvent(new Event('change'));
    fixture.detectChanges();

    element('notificaciones-enviar')!.click();
    const enviado = http.expectOne(
      (request) =>
        request.url === '/web/operador/notificaciones/difusiones' && request.method === 'POST',
    );
    expect(enviado.request.body.titulo).toBe('Aviso');
    enviado.flush(RESULTADO);
    http.expectOne('/web/operador/notificaciones/difusiones').flush({ items: HISTORIAL });
    fixture.detectChanges();

    expect(element('notificaciones-enviadas')?.textContent).toBe(String(RESULTADO.enviadas));
    expect(element('notificaciones-item-' + HISTORIAL[0].difusionId)?.textContent).toContain(
      HISTORIAL[0].titulo,
    );
  });
});
