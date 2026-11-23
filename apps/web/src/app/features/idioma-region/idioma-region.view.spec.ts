import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { defaultLocale, provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { IdiomaRegionView } from './idioma-region.view';

describe('IdiomaRegionView', () => {
  beforeEach(() => localStorage.removeItem('solventa.locale'));
  afterEach(() => localStorage.removeItem('solventa.locale'));

  it('lists the four locales', async () => {
    await TestBed.configureTestingModule({
      imports: [IdiomaRegionView],
      providers: [provideRouter([]), ...provideSolventaI18n()],
    }).compileComponents();
    const fixture = TestBed.createComponent(IdiomaRegionView);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;

    for (const locale of ['es-CO', 'es-MX', 'es-CL', 'es-PE']) {
      expect(host.querySelector(`[data-testid="idioma-region-${locale}"]`)).not.toBeNull();
    }
  });

  it('previews the sample premium and date in the selected locale (HU-108 México)', async () => {
    await TestBed.configureTestingModule({
      imports: [IdiomaRegionView],
      providers: [provideRouter([]), ...provideSolventaI18n()],
    }).compileComponents();
    const fixture = TestBed.createComponent(IdiomaRegionView);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    const text = (id: string) =>
      host.querySelector(`[data-testid="${id}"]`)!.textContent!.replace(/[  ]/g, ' ').trim();

    expect(text('idioma-region-sample-premium')).toBe('$ 1.235 COP');

    host.querySelector<HTMLButtonElement>('[data-testid="idioma-region-es-MX"]')!.click();
    fixture.detectChanges();

    expect(text('idioma-region-sample-premium')).toBe('$1,234.56 MXN');
    expect(text('idioma-region-sample-date')).toBe('09/07/2026');
  });

  it('as a top-level route, Continuar goes to /registro after choosing a locale', async () => {
    await TestBed.configureTestingModule({
      imports: [IdiomaRegionView],
      providers: [provideRouter([{ path: 'registro', children: [] }]), ...provideSolventaI18n()],
    }).compileComponents();
    const fixture = TestBed.createComponent(IdiomaRegionView);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;

    host.querySelector<HTMLButtonElement>('[data-testid="idioma-region-es-MX"]')!.click();
    fixture.detectChanges();
    host.querySelector<HTMLButtonElement>('[data-testid="idioma-region-continue"]')!.click();
    await fixture.whenStable();

    expect(TestBed.inject(Router).url).toBe('/registro');
    expect(localStorage.getItem('solventa.locale')).toBe('es-MX');
  });

  it('as a top-level route, Continuar without picking anything confirms the default locale (regression: used to loop back to idioma-region)', async () => {
    await TestBed.configureTestingModule({
      imports: [IdiomaRegionView],
      providers: [provideRouter([{ path: 'registro', children: [] }]), ...provideSolventaI18n()],
    }).compileComponents();
    const fixture = TestBed.createComponent(IdiomaRegionView);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;

    host.querySelector<HTMLButtonElement>('[data-testid="idioma-region-continue"]')!.click();
    await fixture.whenStable();

    expect(TestBed.inject(Router).url).toBe('/registro');
    expect(localStorage.getItem('solventa.locale')).toBe(defaultLocale);
  });

  it('embedded (Perfil), choosing a locale and Listo emits done instead of navigating', async () => {
    await TestBed.configureTestingModule({
      imports: [IdiomaRegionView],
      providers: [provideRouter([]), ...provideSolventaI18n()],
    }).compileComponents();
    const fixture = TestBed.createComponent(IdiomaRegionView);
    fixture.componentRef.setInput('embedded', true);
    let emitted = false;
    fixture.componentInstance.done.subscribe(() => (emitted = true));
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;

    host.querySelector<HTMLButtonElement>('[data-testid="idioma-region-es-CL"]')!.click();
    fixture.detectChanges();
    host.querySelector<HTMLButtonElement>('[data-testid="idioma-region-done"]')!.click();
    fixture.detectChanges();

    expect(localStorage.getItem('solventa.locale')).toBe('es-CL');
    expect(emitted).toBeTrue();
    expect(TestBed.inject(Router).url).toBe('/');
  });
});
