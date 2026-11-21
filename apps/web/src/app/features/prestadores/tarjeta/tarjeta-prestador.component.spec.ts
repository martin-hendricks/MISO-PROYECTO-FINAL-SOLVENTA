import { TestBed } from '@angular/core/testing';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Prestador } from '../prestadores.gateway';
import { IPS, PRESTADOR } from '../prestadores.testing';
import { TarjetaPrestadorComponent } from './tarjeta-prestador.component';

describe('TarjetaPrestadorComponent', () => {
  function render(prestadores: Prestador[], referencia: 'posicion' | 'evento' | null = 'posicion') {
    TestBed.configureTestingModule({
      imports: [TarjetaPrestadorComponent],
      providers: [...provideSolventaI18n()],
    });
    const fixture = TestBed.createComponent(TarjetaPrestadorComponent);
    fixture.componentRef.setInput('prestadores', prestadores);
    fixture.componentRef.setInput('referencia', referencia);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const porId = (id: string) => host.querySelector<HTMLElement>(`[data-testid="${id}"]`);
    return { fixture, host, porId };
  }

  it('shows the details, the distance, the call link and the directions of one provider', () => {
    const { host, porId } = render([{ ...IPS, distanciaKm: 1.2 }]);
    const dialogo = host.querySelector('[role="dialog"]') as HTMLElement;
    const titulo = host.querySelector(`#${dialogo.getAttribute('aria-labelledby')}`);

    expect(titulo?.textContent?.trim()).toBe('IPS Urgencias Chapinero');
    expect(porId(`tarjeta-fila-${IPS.id}`)?.textContent).toContain('IPS de urgencias');
    expect(porId(`tarjeta-fila-${IPS.id}`)?.textContent).toContain('Cra 13 #45-18 · Chapinero');
    expect(porId(`tarjeta-fila-${IPS.id}`)?.textContent).toContain('Lun–Sáb 7:00–19:00');
    expect(
      Array.from(porId(`tarjeta-ramos-${IPS.id}`)!.querySelectorAll('li')).map((li) =>
        li.textContent?.trim(),
      ),
    ).toEqual(['Microseguro de vida', 'Viaje']);
    expect(porId(`tarjeta-distancia-${IPS.id}`)?.textContent?.trim()).toBe('A 1,2 km');
    expect(porId(`tarjeta-llamar-${IPS.id}`)?.getAttribute('href')).toBe('tel:6015550112');
    expect(porId(`tarjeta-llamar-${IPS.id}`)?.textContent).toContain('601 555 0112');
    expect(porId(`tarjeta-como-llegar-${IPS.id}`)?.getAttribute('href')).toBe(
      `https://www.google.com/maps/dir/?api=1&destination=${IPS.lat},${IPS.lng}`,
    );
    expect(host.querySelectorAll('h3').length).toBe(0);
  });

  it('labels the distance from the event and hides it without an origin', () => {
    const evento = render([PRESTADOR], 'evento');
    expect(evento.porId(`tarjeta-distancia-${PRESTADOR.id}`)?.textContent?.trim()).toBe(
      'A 0,9 km del evento',
    );
    TestBed.resetTestingModule();

    const sinOrigen = render([PRESTADOR], null);
    expect(sinOrigen.porId(`tarjeta-distancia-${PRESTADOR.id}`)).toBeNull();
    TestBed.resetTestingModule();

    const sinDistancia = render([{ ...PRESTADOR, distanciaKm: null }]);
    expect(sinDistancia.porId(`tarjeta-distancia-${PRESTADOR.id}`)).toBeNull();
  });

  it('shows one row per provider of a stack', () => {
    const { host, porId } = render([PRESTADOR, IPS]);
    expect(porId(`tarjeta-fila-${PRESTADOR.id}`)).not.toBeNull();
    expect(porId(`tarjeta-fila-${IPS.id}`)).not.toBeNull();
    expect(host.querySelector('h2')?.textContent?.trim()).toBe('2 prestadores en este punto');
    expect(Array.from(host.querySelectorAll('h3')).map((h) => h.textContent?.trim())).toEqual([
      PRESTADOR.nombre,
      IPS.nombre,
    ]);
  });

  it('closes with the X and with Escape', () => {
    const { fixture, porId } = render([PRESTADOR]);
    let cierres = 0;
    fixture.componentInstance.cerrar.subscribe(() => (cierres += 1));

    const cerrar = porId('tarjeta-cerrar') as HTMLButtonElement;
    expect(cerrar.getAttribute('aria-label')).toBe('Cerrar ficha');
    cerrar.click();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));

    expect(cierres).toBe(2);
  });

  it('moves focus to the heading on open and back to the trigger on close', () => {
    const fila = document.createElement('button');
    document.body.appendChild(fila);
    fila.focus();

    const { fixture, host } = render([PRESTADOR]);
    expect(document.activeElement).toBe(host.querySelector('h2'));

    fixture.destroy();
    expect(document.activeElement).toBe(fila);
    fila.remove();
  });

  it('warns that the directions link opens a new tab', () => {
    const { porId } = render([IPS]);
    const enlace = porId(`tarjeta-como-llegar-${IPS.id}`)!;

    expect(enlace.getAttribute('target')).toBe('_blank');
    expect(enlace.querySelector('.visually-hidden')?.textContent).toContain(
      'se abre en una pestaña nueva',
    );
  });
});
