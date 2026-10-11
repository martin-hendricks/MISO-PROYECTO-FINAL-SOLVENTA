import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  provideRouter,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';
import { redirectSignedIn, requireSession } from './session.guard';
import { SessionService } from './session.service';

describe('session guards', () => {
  function run(guard: typeof requireSession, active: boolean) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: SessionService, useValue: { isActive: () => active } },
      ],
    });
    return TestBed.runInInjectionContext(() =>
      guard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );
  }

  it('sends a visitor without session to login', () => {
    const result = run(requireSession, false);

    expect(result instanceof UrlTree && result.toString()).toBe('/login');
  });

  it('lets a signed-in customer through', () => {
    expect(run(requireSession, true)).toBeTrue();
  });

  it('skips login when the session is already open', () => {
    const result = run(redirectSignedIn, true);

    expect(result instanceof UrlTree && result.toString()).toBe('/user');
  });

  it('shows login to a visitor without session', () => {
    expect(run(redirectSignedIn, false)).toBeTrue();
  });
});
