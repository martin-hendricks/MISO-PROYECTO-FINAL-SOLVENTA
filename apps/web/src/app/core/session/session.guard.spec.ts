import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  CanActivateFn,
  provideRouter,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';
import { redirectSignedIn, requireRole } from './session.guard';
import { Role, SessionService } from './session.service';

describe('session guards', () => {
  const staff: readonly Role[] = ['asesor', 'operador'];

  function run(guard: CanActivateFn, role: Role | null) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        {
          provide: SessionService,
          useValue: { hasRole: (roles: readonly Role[]) => role !== null && roles.includes(role) },
        },
      ],
    });
    return TestBed.runInInjectionContext(() =>
      guard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
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
});
