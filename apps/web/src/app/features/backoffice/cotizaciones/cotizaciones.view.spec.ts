import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { CotizacionesView } from './cotizaciones.view';

describe('CotizacionesView', () => {
  function render(role: Role) {
    TestBed.configureTestingModule({
      imports: [CotizacionesView],
      providers: [provideRouter([]), ...provideSolventaI18n(), sessionAs(role).provider],
    });
    const fixture = TestBed.createComponent(CotizacionesView);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    return {
      host,
      element: (testId: string) => host.querySelector<HTMLElement>(`[data-testid="${testId}"]`),
    };
  }

  it('offers the advisor a new quote', () => {
    const { host, element } = render('asesor');

    expect(host.querySelector('h1')?.textContent).toContain('Cotizaciones');
    expect(host.textContent).toContain('camila.restrepo@solventa.co · Asesor');
    expect(element('section-cotizaciones')?.getAttribute('data-state')).toBe('pending');
    expect(element('cotizaciones-new')?.textContent).toContain('Nueva cotización');
    expect(element('cotizaciones-new')?.getAttribute('href')).toBe('/nueva');
    expect(element('section-pending')).not.toBeNull();
  });

  it('keeps the quotes from the operator', () => {
    const { element } = render('operador');

    expect(element('section-cotizaciones')?.getAttribute('data-state')).toBe('no-permission');
    expect(element('no-permission')?.getAttribute('data-required')).toBe('asesor');
    expect(element('cotizaciones-new')).toBeNull();
  });
});
