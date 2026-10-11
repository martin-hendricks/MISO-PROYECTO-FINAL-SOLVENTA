import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
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

    expect(host.querySelector('[data-testid="nav-user"]')?.getAttribute('href')).toBe('/user');
    expect(host.querySelector('[data-testid="nav-cms"]')).toBeNull();
  });
});
