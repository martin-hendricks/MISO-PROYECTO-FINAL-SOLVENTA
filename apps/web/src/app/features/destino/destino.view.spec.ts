import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { Destino, DestinoView } from './destino.view';

describe('DestinoView', () => {
  function render(destino: Destino, id: string | null, fallo = false) {
    TestBed.configureTestingModule({
      imports: [DestinoView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
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
    const http = TestBed.inject(HttpTestingController);
    if (destino === 'perfil') {
      const perfil = http.expectOne('/web/cliente/perfil');
      if (fallo) {
        perfil.flush({}, { status: 503, statusText: 'Unavailable' });
      } else {
        perfil.flush({
          usuarioId: '11111111-1111-1111-1111-111111111111',
          correo: 'camila@correo.com',
          nombre: 'Camila',
          apellidos: 'Restrepo',
          documento: '1012345678',
        });
      }
      fixture.detectChanges();
    }
    if (destino === 'siniestro' || destino === 'siniestros') {
      const inicio = http.expectOne('/web/cliente/inicio');
      if (fallo) {
        inicio.flush({}, { status: 503, statusText: 'Unavailable' });
      } else {
        inicio.flush({
          ofertaVigente: null,
          poliza: null,
          siniestroEnCurso:
            destino === 'siniestro' ? { siniestroId: 'SIN-1', estado: 'recibido' } : null,
          hipotecario: null,
        });
      }
      fixture.detectChanges();
    }
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
    const toggle = perfil.querySelector('[data-testid="perfil-idioma-region-open"]');
    expect(toggle).not.toBeNull();
    expect(toggle?.getAttribute('aria-expanded')).toBe('false');
    expect(toggle?.getAttribute('aria-controls')).toBe('destino-idioma-region');
    expect(perfil.querySelector('[data-testid="idioma-region"]')).toBeNull();
  });

  it('other destinations do not offer the idioma-region dialog', () => {
    const { host: otro } = render('cotizacion', null);
    expect(otro.querySelector('[data-testid="perfil-idioma-region-open"]')).toBeNull();
  });

  it('shows the profile name and the open claim', () => {
    const { host: perfil } = render('perfil', null);
    expect(perfil.querySelector('[data-testid="perfil-nombre"]')?.textContent).toContain(
      'Camila Restrepo',
    );

    TestBed.resetTestingModule();
    const { host: siniestro } = render('siniestro', null);
    expect(siniestro.querySelector('[data-testid="siniestro-id"]')?.textContent).toContain('SIN-1');
  });

  it('leaves the name and the claim blank when those reads fail or there is no claim', () => {
    const { host: perfil } = render('perfil', null, true);
    expect(perfil.querySelector('[data-testid="perfil-nombre"]')).toBeNull();

    TestBed.resetTestingModule();
    const { host: vacio } = render('siniestros', null);
    expect(vacio.querySelector('[data-testid="siniestro-id"]')).toBeNull();

    TestBed.resetTestingModule();
    const { host: caido } = render('siniestro', null, true);
    expect(caido.querySelector('[data-testid="siniestro-id"]')).toBeNull();
  });

  it('opens the embedded dialog from Perfil and closes it on done', () => {
    const { fixture, host } = render('perfil', null);

    host.querySelector<HTMLButtonElement>('[data-testid="perfil-idioma-region-open"]')!.click();
    fixture.detectChanges();

    expect(
      host
        .querySelector('[data-testid="perfil-idioma-region-open"]')
        ?.getAttribute('aria-expanded'),
    ).toBe('true');
    const dialog = host.querySelector('[data-testid="idioma-region"]');
    expect(dialog).not.toBeNull();
    expect(dialog?.getAttribute('data-embedded')).toBe('true');
    expect(host.querySelector('#destino-idioma-region')).not.toBeNull();

    host.querySelector<HTMLButtonElement>('[data-testid="idioma-region-done"]')!.click();
    fixture.detectChanges();

    expect(host.querySelector('[data-testid="idioma-region"]')).toBeNull();
    expect(
      host
        .querySelector('[data-testid="perfil-idioma-region-open"]')
        ?.getAttribute('aria-expanded'),
    ).toBe('false');
  });
});
