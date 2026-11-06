import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { of } from 'rxjs';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { ConfirmacionTarjetaView } from './confirmacion-tarjeta.view';

describe('ConfirmacionTarjetaView', () => {
  function render(query: Record<string, string> = { cotizacion: 'COT-1042', prima: '42000' }) {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [ConfirmacionTarjetaView],
      providers: [
        provideRouter([]),
        ...provideSolventaI18n(),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { queryParamMap: convertToParamMap(query) },
            queryParamMap: of(convertToParamMap(query)),
          },
        },
      ],
    });
    const navigate = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(ConfirmacionTarjetaView);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const element = (testId: string) => host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { fixture, navigate, element };
  }

  it('shows the premium and keeps confirmation disabled until the local card is complete', () => {
    const { element } = render();
    expect(element('tarjeta-prima')?.textContent).toContain('42.000');
    expect(element('tarjeta-privacidad')?.textContent).toContain('no se envían');
    expect(element('tarjeta-titular')?.getAttribute('placeholder')).toBe('Camila Restrepo');
    expect(element('tarjeta-numero')?.getAttribute('placeholder')).toBe('4242 4242 4242 4242');
    expect(element('tarjeta-mes')?.getAttribute('placeholder')).toBe('08');
    expect(element('tarjeta-anio')?.getAttribute('placeholder')).toBe('28');
    expect(element('tarjeta-codigo')?.getAttribute('placeholder')).toBe('123');
    expect(element('tarjeta-numero-hint')?.textContent).toContain('16 dígitos');
    expect((element('tarjeta-confirmar') as HTMLButtonElement).disabled).toBeTrue();
    (element('confirmacion-tarjeta')!.querySelector('form') as HTMLFormElement).dispatchEvent(
      new Event('submit', { cancelable: true }),
    );
    element('tarjeta-volver')!.click();
    element('tarjeta-cancelar')!.click();
  });

  it('continues to issuance with only the quote id', () => {
    const { fixture, navigate, element } = render();
    const type = (testId: string, value: string) => {
      const input = element(testId) as HTMLInputElement;
      input.value = value;
      input.dispatchEvent(new Event('input'));
      fixture.detectChanges();
    };
    type('tarjeta-titular', 'Camila Restrepo');
    type('tarjeta-numero', '4242424242424242');
    type('tarjeta-mes', '8');
    type('tarjeta-anio', '28');
    type('tarjeta-codigo', '123');
    element('tarjeta-confirmar')!.dispatchEvent(new Event('click'));
    (element('confirmacion-tarjeta')!.querySelector('form') as HTMLFormElement).dispatchEvent(
      new Event('submit', { cancelable: true }),
    );
    expect(navigate).toHaveBeenCalledWith(['/emision'], { queryParams: { cotizacion: 'COT-1042' } });
    expect(JSON.stringify(navigate.calls.mostRecent().args)).not.toContain('4242');
  });

  it('hides the premium when the offer did not pass one', () => {
    const { element, navigate } = render({});
    expect(element('tarjeta-prima')).toBeNull();
    (element('confirmacion-tarjeta')!.querySelector('form') as HTMLFormElement).dispatchEvent(
      new Event('submit', { cancelable: true }),
    );
    expect(navigate).not.toHaveBeenCalled();
  });
});
