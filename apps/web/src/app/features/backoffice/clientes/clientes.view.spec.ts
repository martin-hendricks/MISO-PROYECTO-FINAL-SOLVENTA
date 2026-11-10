import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { CLIENTES } from './clientes.testing';
import { ClientesView } from './clientes.view';

describe('ClientesView', () => {
  function render(role: Role) {
    TestBed.configureTestingModule({
      imports: [ClientesView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
      ],
    });
    const fixture = TestBed.createComponent(ClientesView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) => host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, http, host, element };
  }

  function listado(role: Role = 'operador') {
    const rendered = render(role);
    const request = rendered.http.expectOne(
      (candidate) =>
        candidate.url === '/web/operador/clientes' && candidate.params.get('pagina') === '1',
    );
    request.flush({ clientes: CLIENTES, pagina: 1, hayMas: false });
    rendered.fixture.detectChanges();
    return rendered;
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('shows push states and hides write controls for the advisor', () => {
    const { element } = listado('asesor');
    const activo = CLIENTES[0].usuarioId;
    const sinPush = CLIENTES[1].usuarioId;
    const desconocido = CLIENTES[2].usuarioId;

    expect(element(`push-${activo}`)?.getAttribute('data-push')).toBe('si');
    expect(element(`push-${sinPush}`)?.textContent).toContain('No');
    expect(element(`push-${desconocido}`)?.textContent).toContain('Desconocido');
    expect(element('clientes-new')).toBeNull();
    expect(element(`editar-${activo}`)).toBeNull();
    expect(element(`desactivar-${activo}`)).toBeNull();
    expect(element(`cotizar-${activo}`)?.getAttribute('href')).toContain(`cliente=${activo}`);
    expect(element(`cotizar-${desconocido}`)).toBeNull();
  });

  it('lets the operator open the create form', () => {
    const { fixture, element } = listado('operador');

    element('clientes-new')!.click();
    fixture.detectChanges();

    expect(element('clientes-form')).not.toBeNull();
    expect((element('clientes-save') as HTMLButtonElement).disabled).toBeTrue();
  });

  it('shows the empty state when the page has no clients', () => {
    const { fixture, http, element } = render('asesor');
    http
      .expectOne((candidate) => candidate.url === '/web/operador/clientes')
      .flush({ clientes: [], pagina: 1, hayMas: false });
    fixture.detectChanges();

    expect(element('clientes-empty')).not.toBeNull();
    expect(element('clientes-table')).toBeNull();
  });

  it('offers to retry in the same view when the list fails', () => {
    const { fixture, http, element } = render('asesor');
    http.expectOne((candidate) => candidate.url === '/web/operador/clientes').error(new ProgressEvent('error'));
    fixture.detectChanges();

    element('clientes-retry')!.click();
    http
      .expectOne((candidate) => candidate.url === '/web/operador/clientes')
      .flush({ clientes: CLIENTES, pagina: 1, hayMas: false });
    fixture.detectChanges();

    expect(element('clientes-error')).toBeNull();
    expect(element('clientes-table')).not.toBeNull();
  });
});
