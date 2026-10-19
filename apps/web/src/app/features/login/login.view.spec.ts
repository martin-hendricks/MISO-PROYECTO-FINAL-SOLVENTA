import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter, Router } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { SESSION_STORAGE_KEY } from '../../core/session/session.service';
import { fakeTokenPair } from '../../core/session/session.testing';
import { BACKOFFICE_LOGIN, CUSTOMER_LOGIN, LoginVariant } from './login.variant';
import { LoginView } from './login.view';

describe('LoginView', () => {
  let fixture: ComponentFixture<LoginView>;
  let http: HttpTestingController;
  let navigate: jasmine.Spy;

  const element = (testId: string) =>
    (fixture.nativeElement as HTMLElement).querySelector<HTMLElement>(`[data-testid="${testId}"]`);

  function type(testId: string, value: string): void {
    const input = element(testId) as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
  }

  function submit(): void {
    element('login-form')!.dispatchEvent(new Event('submit', { cancelable: true }));
    fixture.detectChanges();
  }

  async function open(variant: LoginVariant): Promise<void> {
    await TestBed.configureTestingModule({
      imports: [LoginView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
        { provide: ActivatedRoute, useValue: { snapshot: { data: { login: variant } } } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(LoginView);
    http = TestBed.inject(HttpTestingController);
    navigate = spyOn(TestBed.inject(Router), 'navigateByUrl').and.resolveTo(true);
    fixture.detectChanges();
  }

  beforeEach(() => sessionStorage.removeItem(SESSION_STORAGE_KEY));

  afterEach(() => {
    http.verify();
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
  });

  describe('customer portal', () => {
    beforeEach(() => open(CUSTOMER_LOGIN));

    it('opens the customer home after valid credentials', () => {
      type('login-email', 'camila@correo.com');
      type('login-password', 'secreto');
      submit();

      const request = http.expectOne('/web/sesion/ingreso');
      expect(request.request.body).toEqual({
        correo: 'camila@correo.com',
        contrasena: 'secreto',
        rol: 'cliente',
      });
      request.flush(fakeTokenPair());

      expect(navigate).toHaveBeenCalledOnceWith('/user');
    });

    it('shows the error in the same view on invalid credentials', () => {
      type('login-email', 'camila@correo.com');
      type('login-password', 'incorrecta');
      submit();
      http
        .expectOne('/web/sesion/ingreso')
        .flush({ detail: 'Credenciales invalidas' }, { status: 401, statusText: 'Unauthorized' });
      fixture.detectChanges();

      expect(element('login-error')?.getAttribute('data-kind')).toBe('credentials');
      expect(element('login-error')?.textContent).toContain('Correo o contraseña incorrectos.');
      expect((element('login-email') as HTMLInputElement).value).toBe('camila@correo.com');
      expect(navigate).not.toHaveBeenCalled();
    });

    it('shows the error in the same view on a network failure', () => {
      type('login-email', 'camila@correo.com');
      type('login-password', 'secreto');
      submit();
      http.expectOne('/web/sesion/ingreso').error(new ProgressEvent('error'));
      fixture.detectChanges();

      expect(element('login-error')?.getAttribute('data-kind')).toBe('network');
      expect(navigate).not.toHaveBeenCalled();
    });

    it('marks empty fields inline without calling the BFF', () => {
      submit();

      expect(element('login-email-error')).not.toBeNull();
      expect(element('login-password-error')).not.toBeNull();
      expect(element('login-email')?.getAttribute('aria-invalid')).toBe('true');
      http.expectNone('/web/sesion/ingreso');
    });

    it('disables the submit button while signing in', () => {
      type('login-email', 'camila@correo.com');
      type('login-password', 'secreto');
      submit();

      expect((element('login-submit') as HTMLButtonElement).disabled).toBeTrue();

      http.expectOne('/web/sesion/ingreso').flush(fakeTokenPair());
    });

    it('offers to create an account', () => {
      expect(element('login-register')).not.toBeNull();
    });
  });

  describe('back-office', () => {
    beforeEach(() => open(BACKOFFICE_LOGIN));

    it('opens the back-office without choosing a role', () => {
      type('login-email', 'camila.restrepo@solventa.co');
      type('login-password', 'secreto');
      submit();

      const request = http.expectOne('/web/sesion/ingreso');
      expect(request.request.body).toEqual({
        correo: 'camila.restrepo@solventa.co',
        contrasena: 'secreto',
      });
      request.flush(fakeTokenPair('asesor'));

      expect(navigate).toHaveBeenCalledOnceWith('/cms');
    });

    it('explains that Solventa assigns the role and hides account creation', () => {
      expect((fixture.nativeElement as HTMLElement).textContent).toContain(
        'El rol (asesor u operador) lo asigna Solventa.',
      );
      expect(element('login-register')).toBeNull();
    });
  });
});
