import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { MOTIVO } from '../emision.testing';
import { SuscripcionRechazadaView } from './suscripcion-rechazada.view';

describe('SuscripcionRechazadaView', () => {
  const initialState = history.state;

  function render(state: unknown) {
    history.replaceState(state, '');
    TestBed.configureTestingModule({
      imports: [SuscripcionRechazadaView],
      providers: [provideRouter([]), ...provideSolventaI18n()],
    });
    const fixture = TestBed.createComponent(SuscripcionRechazadaView);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { host, element };
  }

  afterEach(() => history.replaceState(initialState, ''));

  it('shows the reason stored by the core and a way back to Inicio', () => {
    const { host, element } = render({ motivo: MOTIVO });

    expect(element('rechazo-motivo')?.textContent).toContain(MOTIVO.mensaje);
    expect(element('rechazo-inicio')?.getAttribute('href')).toBe('/');
    expect(host.textContent).not.toContain('POL-');
  });

  it('still explains the rejection when the reason is no longer in the navigation', () => {
    const { element } = render(null);

    expect(element('suscripcion-rechazada')).not.toBeNull();
    expect(element('rechazo-motivo')).toBeNull();
    expect(element('rechazo-inicio')?.getAttribute('href')).toBe('/');
  });
});
