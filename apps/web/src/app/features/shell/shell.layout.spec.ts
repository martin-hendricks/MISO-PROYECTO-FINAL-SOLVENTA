import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { SessionService } from '../../core/session/session.service';
import { ShellLayout } from './shell.layout';

describe('ShellLayout', () => {
  it('links the customer shell', async () => {
    await TestBed.configureTestingModule({
      imports: [ShellLayout],
      providers: [provideRouter([]), ...provideSolventaI18n()],
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

  it('opens the hamburger overlay with the same four destinations', async () => {
    await TestBed.configureTestingModule({
      imports: [ShellLayout],
      providers: [provideRouter([]), ...provideSolventaI18n()],
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
    expect(overlay!.querySelector('[data-testid="nav-menu-perfil"]')?.getAttribute('href')).toBe(
      '/perfil',
    );
  });

  it('closing the overlay does not navigate away from the current page', async () => {
    await TestBed.configureTestingModule({
      imports: [ShellLayout],
      providers: [provideRouter([]), ...provideSolventaI18n()],
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
});
