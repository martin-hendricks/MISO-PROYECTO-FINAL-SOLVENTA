import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  provideRouter,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';
import { Alta, RegistroDraft, requireDraft } from './registro.draft';

describe('RegistroDraft', () => {
  const ALTA: Alta = {
    nombre: 'Camila',
    apellidos: 'Restrepo',
    documento: '1012345678',
    correo: 'camila@correo.com',
    contrasena: 'secreto123',
  };

  function guard() {
    return TestBed.runInInjectionContext(() =>
      requireDraft({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );
  }

  beforeEach(() => TestBed.configureTestingModule({ providers: [provideRouter([])] }));

  it('lets the customer reach consent with the sign-up data', () => {
    TestBed.inject(RegistroDraft).save(ALTA);

    expect(guard()).toBeTrue();
  });

  it('sends the customer back to sign-up when there is no data', () => {
    const draft = TestBed.inject(RegistroDraft);
    draft.save(ALTA);
    draft.clear();

    const result = guard();

    expect(result instanceof UrlTree && result.toString()).toBe('/registro');
  });
});
