import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { SessionService } from '../../core/session/session.service';
import { PerfilGateway } from '../perfil/perfil.gateway';
import { ShellLayout } from './shell.layout';

/** Every test injects this: ShellLayout loads the profile on construction
 * (for the avatar initials), and these specs are not about that flow. */
const stubPerfilGateway = { provide: PerfilGateway, useValue: { load: () => of(null) } };

describe('ShellLayout', () => {
  it('links the customer shell', async () => {
    await TestBed.configureTestingModule({
      imports: [ShellLayout],
      providers: [provideRouter([]), ...provideSolventaI18n(), stubPerfilGateway],
    }).compileComponents();
    const fixture = TestBed.createComponent(ShellLayout);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;

    expect(host.querySelector('[data-testid="nav-inicio"]')?.getAttribute('href')).toBe('/inicio');
    expect(host.querySelector('[data-testid="nav-polizas"]')?.getAttribute('href')).toBe(
      '/polizas',
    );
    expect(host.querySelector('[data-testid="nav-siniestros"]')?.getAttribute('href')).toBe(
      '/siniestros',
    );
    expect(host.querySelector('[data-testid="nav-billetera"]')?.getAttribute('href')).toBe(
      '/billetera',
    );
    expect(host.querySelector('[data-testid="nav-perfil"]')?.getAttribute('href')).toBe('/perfil');
    expect(host.querySelector('[data-testid="header-new-quote"]')?.getAttribute('href')).toBe(
      '/cotizacion',
    );
    expect(host.querySelector('[data-testid="nav-cms"]')).toBeNull();
  });

  it('closes the session and returns to the customer login', async () => {
    const signOut = jasmine.createSpy('signOut');
    await TestBed.configureTestingModule({
      imports: [ShellLayout],
      providers: [
        provideRouter([{ path: 'login', children: [] }]),
        ...provideSolventaI18n(),
        { provide: SessionService, useValue: { signOut } },
        stubPerfilGateway,
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(ShellLayout);
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="sign-out"]')!
      .click();
    await fixture.whenStable();

    expect(signOut).toHaveBeenCalledTimes(1);
    expect(TestBed.inject(Router).url).toBe('/login');
  });

  it('opens the hamburger overlay with the same five destinations', async () => {
    await TestBed.configureTestingModule({
      imports: [ShellLayout],
      providers: [provideRouter([]), ...provideSolventaI18n(), stubPerfilGateway],
    }).compileComponents();
    const fixture = TestBed.createComponent(ShellLayout);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;

    expect(host.querySelector('[data-testid="nav-menu-overlay"]')).toBeNull();

    host.querySelector<HTMLButtonElement>('[data-testid="nav-menu-toggle"]')!.click();
    fixture.detectChanges();

    const overlay = host.querySelector('[data-testid="nav-menu-overlay"]');
    expect(overlay).not.toBeNull();
    expect(overlay!.querySelector('[data-testid="nav-menu-inicio"]')?.getAttribute('href')).toBe(
      '/inicio',
    );
    expect(overlay!.querySelector('[data-testid="nav-menu-polizas"]')?.getAttribute('href')).toBe(
      '/polizas',
    );
    expect(
      overlay!.querySelector('[data-testid="nav-menu-siniestros"]')?.getAttribute('href'),
    ).toBe('/siniestros');
    expect(overlay!.querySelector('[data-testid="nav-menu-billetera"]')?.getAttribute('href')).toBe(
      '/billetera',
    );
    expect(overlay!.querySelector('[data-testid="nav-menu-perfil"]')?.getAttribute('href')).toBe(
      '/perfil',
    );
  });

  it('shows the initials of the logged-in customer next to sign out', async () => {
    await TestBed.configureTestingModule({
      imports: [ShellLayout],
      providers: [
        provideRouter([]),
        ...provideSolventaI18n(),
        {
          provide: PerfilGateway,
          useValue: {
            load: () =>
              of({
                usuarioId: 'u1',
                correo: 'camila@correo.com',
                nombre: 'Camila',
                apellidos: 'Restrepo',
                documento: '123',
              }),
          },
        },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(ShellLayout);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const avatar = (fixture.nativeElement as HTMLElement).querySelector('[data-testid="avatar"]');
    expect(avatar?.textContent?.trim()).toBe('CR');
    expect(avatar?.getAttribute('title')).toBe('Camila Restrepo');
    expect(avatar?.getAttribute('role')).toBe('img');
    expect(avatar?.getAttribute('aria-label')).toBe('Camila Restrepo');
  });

  it('leaves the avatar empty if the profile fails to load, without crashing', async () => {
    await TestBed.configureTestingModule({
      imports: [ShellLayout],
      providers: [
        provideRouter([]),
        ...provideSolventaI18n(),
        { provide: PerfilGateway, useValue: { load: () => throwError(() => new Error('caida')) } },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(ShellLayout);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const avatar = (fixture.nativeElement as HTMLElement).querySelector('[data-testid="avatar"]');
    expect(avatar?.textContent?.trim()).toBe('');
    expect(avatar?.getAttribute('role')).toBeNull();
    expect(avatar?.getAttribute('aria-label')).toBeNull();
  });

  it('closing the overlay does not navigate away from the current page', async () => {
    await TestBed.configureTestingModule({
      imports: [ShellLayout],
      providers: [provideRouter([]), ...provideSolventaI18n(), stubPerfilGateway],
    }).compileComponents();
    const fixture = TestBed.createComponent(ShellLayout);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const router = TestBed.inject(Router);
    const urlBeforeClose = router.url;

    host.querySelector<HTMLButtonElement>('[data-testid="nav-menu-toggle"]')!.click();
    fixture.detectChanges();
    host.querySelector<HTMLButtonElement>('[data-testid="nav-menu-close"]')!.click();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(host.querySelector('[data-testid="nav-menu-overlay"]')).toBeNull();
    expect(router.url).toBe(urlBeforeClose);
  });

  describe('accessibility', () => {
    async function render() {
      await TestBed.configureTestingModule({
        imports: [ShellLayout],
        providers: [provideRouter([]), ...provideSolventaI18n(), stubPerfilGateway],
      }).compileComponents();
      const fixture = TestBed.createComponent(ShellLayout);
      document.body.appendChild(fixture.nativeElement);
      fixture.detectChanges();
      const host = fixture.nativeElement as HTMLElement;
      return { fixture, host, q: (id: string) => host.querySelector<HTMLElement>(`[data-testid="${id}"]`) };
    }

    it('skips to the main content without changing the URL', async () => {
      const { q, host } = await render();
      const router = TestBed.inject(Router);
      const urlBefore = router.url;

      q('skip-link')!.click();

      expect(document.activeElement).toBe(q('contenido-principal'));
      expect(host.querySelector('main')?.id).toBe('contenido-principal');
      expect(router.url).toBe(urlBefore);
      host.remove();
    });

    it('ties the menu toggle to the overlay and closes it with Escape', async () => {
      const { fixture, q, host } = await render();

      expect(q('nav-menu-toggle')?.getAttribute('aria-controls')).toBe('nav-overlay');
      q('nav-menu-toggle')!.click();
      fixture.detectChanges();
      expect(q('nav-menu-overlay')?.id).toBe('nav-overlay');

      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
      fixture.detectChanges();

      expect(q('nav-menu-overlay')).toBeNull();
      host.remove();
    });
  });
});
