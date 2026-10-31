import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { Destino, DestinoView } from './destino.view';

describe('DestinoView', () => {
  function render(destino: Destino, id: string | null) {
    TestBed.configureTestingModule({
      imports: [DestinoView],
      providers: [
        provideRouter([]),
        ...provideSolventaI18n(),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { data: { destino }, paramMap: convertToParamMap(id ? { id } : {}) },
          },
        },
      ],
    });
    const fixture = TestBed.createComponent(DestinoView);
    fixture.detectChanges();
    return { fixture, host: fixture.nativeElement as HTMLElement };
  }

  it('names the pending destination with the id Inicio sent', () => {
    const { host } = render('emision', 'COT-1042');

    const section = host.querySelector('[data-testid="destino-emision"]');
    expect(section?.getAttribute('data-id')).toBe('COT-1042');
    expect(section?.querySelector('h1')?.textContent).toContain('Emisión de la póliza');
    expect(host.querySelector('[data-testid="destino-home"]')?.getAttribute('href')).toBe(
      '/inicio',
    );
  });

  it('omits the id when the destination has none', () => {
    const { host } = render('cotizacion', null);

    expect(host.querySelector('[data-testid="destino-cotizacion"]')).not.toBeNull();
    expect(host.querySelector('.subtitle')).toBeNull();
  });

  it('Perfil offers the idioma-region dialog, closed by default', () => {
    const { host: perfil } = render('perfil', null);
    expect(perfil.querySelector('[data-testid="perfil-idioma-region-open"]')).not.toBeNull();
    expect(perfil.querySelector('[data-testid="idioma-region"]')).toBeNull();
  });

  it('other destinations do not offer the idioma-region dialog', () => {
    const { host: otro } = render('cotizacion', null);
    expect(otro.querySelector('[data-testid="perfil-idioma-region-open"]')).toBeNull();
  });

  it('opens the embedded dialog from Perfil and closes it on done', () => {
    const { fixture, host } = render('perfil', null);

    host.querySelector<HTMLButtonElement>('[data-testid="perfil-idioma-region-open"]')!.click();
    fixture.detectChanges();

    const dialog = host.querySelector('[data-testid="idioma-region"]');
    expect(dialog).not.toBeNull();
    expect(dialog?.getAttribute('data-embedded')).toBe('true');

    host.querySelector<HTMLButtonElement>('[data-testid="idioma-region-done"]')!.click();
    fixture.detectChanges();

    expect(host.querySelector('[data-testid="idioma-region"]')).toBeNull();
  });
});
