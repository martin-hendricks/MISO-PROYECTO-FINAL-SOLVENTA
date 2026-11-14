import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { ASISTIDO, AUTOMATICO } from '../billetera.testing';
import { BilleteraDetalleView } from './billetera-detalle.view';

describe('BilleteraDetalleView', () => {
  function render(id: string) {
    TestBed.configureTestingModule({
      imports: [BilleteraDetalleView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ id }) } },
        },
      ],
    });
    const fixture = TestBed.createComponent(BilleteraDetalleView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const element = (testId: string) =>
      (fixture.nativeElement as HTMLElement).querySelector(`[data-testid="${testId}"]`);
    return { fixture, http, element };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('shows an assisted deposit and links the claim', () => {
    const { fixture, http, element } = render(ASISTIDO.id);
    http.expectOne(`/web/cliente/billetera/${ASISTIDO.id}`).flush(ASISTIDO);
    fixture.detectChanges();
    expect(element('billetera-detalle-monto')?.textContent).toContain('890.000');
    expect(element('billetera-ver-siniestro')?.getAttribute('href')).toBe(`/siniestros/${ASISTIDO.id}`);
  });

  it('links an automatic payment to the parametric view', () => {
    const { fixture, http, element } = render(AUTOMATICO.id);
    http.expectOne(`/web/cliente/billetera/${AUTOMATICO.id}`).flush(AUTOMATICO);
    fixture.detectChanges();
    expect(element('billetera-ver-siniestro')?.getAttribute('href')).toBe('/siniestros/parametrico');
  });

  it('reads an empty id when the route has none', () => {
    TestBed.configureTestingModule({
      imports: [BilleteraDetalleView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({}) } },
        },
      ],
    });
    const fixture = TestBed.createComponent(BilleteraDetalleView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne('/web/cliente/billetera/').flush({}, { status: 404, statusText: 'Not Found' });
    fixture.detectChanges();
  });

  it('says the deposit is missing', () => {
    const { fixture, http, element } = render('ausente');
    http.expectOne('/web/cliente/billetera/ausente').flush({}, { status: 404, statusText: 'Not Found' });
    fixture.detectChanges();
    expect(element('billetera-detalle-ausente')).not.toBeNull();
  });

  it('retries after a failure', () => {
    const { fixture, http, element } = render(ASISTIDO.id);
    http.expectOne(`/web/cliente/billetera/${ASISTIDO.id}`).error(new ProgressEvent('error'));
    fixture.detectChanges();
    const retry = (fixture.nativeElement as HTMLElement).querySelector('button');
    expect(element('billetera-detalle-error')).not.toBeNull();
    retry?.click();
    http.expectOne(`/web/cliente/billetera/${ASISTIDO.id}`).flush({ ...ASISTIDO, resumen: '' });
    fixture.detectChanges();
    expect(element('billetera-detalle-monto')).not.toBeNull();
  });
});