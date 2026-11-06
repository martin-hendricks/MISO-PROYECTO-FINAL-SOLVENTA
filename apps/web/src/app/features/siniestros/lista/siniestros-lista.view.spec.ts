import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { SINIESTROS } from '../siniestros.testing';
import { SiniestrosListaView } from './siniestros-lista.view';
import { SiniestrosListaViewModel } from './siniestros-lista.viewmodel';
import { of, throwError } from 'rxjs';

describe('SiniestrosListaView', () => {
  function render() {
    TestBed.configureTestingModule({
      imports: [SiniestrosListaView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
      ],
    });
    const fixture = TestBed.createComponent(SiniestrosListaView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (id: string) => host.querySelector<HTMLElement>(`[data-testid="${id}"]`);
    return { fixture, http, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('muestra cada caso con el estado del núcleo, sin acciones de aprobar ni pagar', () => {
    const { fixture, http, element } = render();
    http.expectOne('/web/cliente/siniestros').flush({ siniestros: SINIESTROS });
    fixture.detectChanges();

    expect(element('siniestro-SIN-2041')?.textContent).toContain('En evaluación');
    expect(element('siniestro-SIN-1988')?.textContent).toContain('Pagado');
    expect(element('siniestro-SIN-1988')?.textContent).toContain('420.000');
    expect(element('siniestros-reportar')?.getAttribute('href')).toBe('/siniestros/nuevo');
    expect(element('siniestros-lista')?.textContent).not.toContain('Aprobar');
  });

  it('muestra cargando, el error con reintento y guiones si faltan fecha o reserva', () => {
    const { fixture, http, element } = render();
    expect(element('siniestros-loading')).not.toBeNull();
    http.expectOne('/web/cliente/siniestros').flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(element('siniestros-error')).not.toBeNull();

    element('siniestros-retry')!.click();
    http
      .expectOne('/web/cliente/siniestros')
      .flush({ siniestros: [{ ...SINIESTROS[0], fecha: null, reserva: null }] });
    fixture.detectChanges();
    expect(element('siniestro-SIN-2041')?.textContent).toContain('—');
  });

  it('muestra el estado vacío', () => {
    const { fixture, http, element } = render();
    http.expectOne('/web/cliente/siniestros').flush({ siniestros: [] });
    fixture.detectChanges();
    expect(element('siniestros-empty')).not.toBeNull();
  });
});

describe('SiniestrosListaViewModel', () => {
  it('pasa a error y se recupera al reintentar', () => {
    let intentos = 0;
    const vm = new SiniestrosListaViewModel(() =>
      ++intentos === 1 ? throwError(() => new Error('sin red')) : of(SINIESTROS),
    );
    vm.load();
    expect(vm.status()).toBe('error');
    vm.load();
    expect(vm.status()).toBe('ready');
    expect(vm.siniestros().length).toBe(2);
  });
});
