import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  CanActivateFn,
  provideRouter,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';
import { LocaleService } from '../i18n/locale.service';
import { redirectSignedIn, requireLocaleChosen, requireRole } from './session.guard';
import { Role, SessionService } from './session.service';

describe('session guards', () => {
  const staff: readonly Role[] = ['asesor', 'operador'];

  function run(guard: CanActivateFn, role: Role | null) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        {
          provide: SessionService,
          useValue: {
            hasRole: (roles: readonly Role[]) => role !== null && roles.includes(role),
            isActive: () => role !== null,
          },
        },
      ],
    });
    return TestBed.runInInjectionContext(() =>
      guard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );
  }

  function runLocaleChosen(hasChosen: boolean, signedIn: boolean) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: SessionService, useValue: { isActive: () => signedIn } },
        { provide: LocaleService, useValue: { hasChosen: () => hasChosen } },
      ],
    });
    return TestBed.runInInjectionContext(() =>
      requireLocaleChosen({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );
  }

  it('sends a visitor without session to the login of the area', () => {
    const result = run(requireRole(staff, '/cms/login'), null);

    expect(result instanceof UrlTree && result.toString()).toBe('/cms/login');
  });

  it('sends a customer away from the back-office', () => {
    const result = run(requireRole(staff, '/cms/login'), 'cliente');

    expect(result instanceof UrlTree && result.toString()).toBe('/cms/login');
  });

  it('lets an allowed role through', () => {
    expect(run(requireRole(staff, '/cms/login'), 'operador')).toBeTrue();
  });

  it('skips login when the session of the area is already open', () => {
    const result = run(redirectSignedIn(['cliente'], '/user'), 'cliente');

    expect(result instanceof UrlTree && result.toString()).toBe('/user');
  });

  it('shows login to a session of another area', () => {
    expect(run(redirectSignedIn(['cliente'], '/user'), 'asesor')).toBeTrue();
  });

  it('sends a first-time visitor to idioma-region', () => {
    const result = runLocaleChosen(false, false);

    expect(result instanceof UrlTree && result.toString()).toBe('/idioma-region');
  });

  it('lets a visitor who already chose a locale through', () => {
    expect(runLocaleChosen(true, false)).toBeTrue();
  });

  it('lets a returning signed-in customer through even without a stored choice', () => {
    expect(runLocaleChosen(false, true)).toBeTrue();
  });
});
