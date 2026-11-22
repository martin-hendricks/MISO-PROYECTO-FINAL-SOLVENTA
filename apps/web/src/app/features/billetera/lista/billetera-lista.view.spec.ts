import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { BILLETERA } from '../billetera.testing';
import { BilleteraListaView } from './billetera-lista.view';

describe('BilleteraListaView', () => {
  const URL = '/web/cliente/billetera';

  function render() {
    TestBed.configureTestingModule({
      imports: [BilleteraListaView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
      ],
    });
    const fixture = TestBed.createComponent(BilleteraListaView);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const element = (testId: string) =>
      (fixture.nativeElement as HTMLElement).querySelector(`[data-testid="${testId}"]`);
    return { fixture, http, element };
  }

  function filas(fixture: { nativeElement: HTMLElement }): string[] {
    return [...fixture.nativeElement.querySelectorAll('[data-testid="billetera-fila"] th')].map(
      (cell) => cell.textContent?.trim() ?? '',
    );
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('shows the total and both deposits', () => {
    const { fixture, http, element } = render();
    expect(element('billetera-loading')).not.toBeNull();
    http.expectOne(URL).flush(BILLETERA);
    fixture.detectChanges();
    expect(element('billetera-total')?.textContent).toContain('1.070.000');
    expect((fixture.nativeElement as HTMLElement).querySelectorAll('[data-testid="billetera-fila"]').length).toBe(
      2,
    );
  });

  it('explains an empty wallet', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({ moneda: 'COP', totalRecibido: 0, movimientos: [] });
    fixture.detectChanges();
    expect(element('billetera-vacia')).not.toBeNull();
    expect(element('billetera-total')).toBeNull();
  });

  it('totals the region currency and lists the other currencies under Otras monedas', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).flush({
      moneda: null,
      totalRecibido: null,
      movimientos: [BILLETERA.movimientos[0], { ...BILLETERA.movimientos[1], moneda: 'MXN' }],
    });
    fixture.detectChanges();

    const chips = [...(fixture.nativeElement as HTMLElement).querySelectorAll('.chip')].map((chip) =>
      chip.textContent?.trim(),
    );
    expect(chips).toEqual(['Todos', 'Asistido', 'Otras monedas', 'Pago automático']);
    expect(element('billetera-total')?.textContent).toContain('890.000');
    expect(filas(fixture)).toEqual(['SIN-1988']);

    (element('chip-otras') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(element('chip-otras')?.getAttribute('aria-pressed')).toBe('true');
    expect(element('billetera-total')).toBeNull();
    expect(filas(fixture)).toEqual(['SIN-1002']);
  });

  it('offers a retry and hides the total when the read fails', () => {
    const { fixture, http, element } = render();
    http.expectOne(URL).error(new ProgressEvent('error'));
    fixture.detectChanges();
    expect(element('billetera-reintentar')).not.toBeNull();
    expect(element('billetera-total')).toBeNull();

    (element('billetera-reintentar') as HTMLButtonElement).click();
    http.expectOne(URL).flush(BILLETERA);
    fixture.detectChanges();
    expect(element('billetera-total')).not.toBeNull();
  });
});
