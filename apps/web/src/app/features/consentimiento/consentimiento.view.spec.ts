import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { SESSION_STORAGE_KEY, SessionService } from '../../core/session/session.service';
import { fakeTokenPair } from '../../core/session/session.testing';
import { CUSTOMER_LOGIN } from '../login/login.variant';
import { Alta, RegistroDraft } from '../registro/registro.draft';
import { ConsentimientoView } from './consentimiento.view';

describe('ConsentimientoView', () => {
  const ALTA: Alta = {
    nombre: 'Camila',
    apellidos: 'Restrepo',
    documento: '1012345678',
    correo: 'camila@correo.com',
    contrasena: 'secreto123',
  };
  const MARCA = { habeasData: true, otorgadoEn: '2026-10-21T15:00:00+00:00', version: '2026-10' };

  let fixture: ComponentFixture<ConsentimientoView>;
  let http: HttpTestingController;
  let navigate: jasmine.Spy;

  const host = () => fixture.nativeElement as HTMLElement;
  const element = (testId: string) =>
    host().querySelector<HTMLElement>(`[data-testid="${testId}"]`);

  function accept(): void {
    const box = element('consentimiento-accept') as HTMLInputElement;
    box.checked = true;
    box.dispatchEvent(new Event('change'));
  }

  function submit(): void {
    element('consentimiento')!.dispatchEvent(new Event('submit', { cancelable: true }));
    fixture.detectChanges();
  }

  beforeEach(async () => {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    await TestBed.configureTestingModule({
      imports: [ConsentimientoView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
      ],
    }).compileComponents();
    TestBed.inject(RegistroDraft).save(ALTA);
    fixture = TestBed.createComponent(ConsentimientoView);
    http = TestBed.inject(HttpTestingController);
    navigate = spyOn(TestBed.inject(Router), 'navigateByUrl').and.resolveTo(true);
    fixture.detectChanges();
  });

  afterEach(() => {
    http.verify();
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
  });

  it('shows the data treatment the customer authorizes', () => {
    expect(element('consentimiento')?.textContent).toContain('Consentimiento de datos');
    expect(element('consentimiento-accept')?.closest('label')?.textContent).toContain(
      'Acepto la política de datos',
    );
    expect((element('consentimiento-accept') as HTMLInputElement).checked).toBeFalse();
  });

  it('asks for the policy without creating the account', () => {
    submit();

    http.expectNone(() => true);
    expect(element('consentimiento-accept')?.getAttribute('aria-invalid')).toBe('true');
    expect(element('consentimiento-accept-error')?.textContent).toContain(
      'Acepta la política de datos para crear tu cuenta.',
    );
    expect(navigate).not.toHaveBeenCalled();
  });

  it('signs up with habeas data, opens the session and lands on the home', () => {
    accept();
    submit();

    const request = http.expectOne('/web/registro');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ ...ALTA, habeasData: true });
    fixture.detectChanges();
    expect(element('consentimiento-submit')?.textContent).toContain('Autorizando');

    request.flush({ ...fakeTokenPair('cliente'), cliente: ALTA, consentimiento: MARCA });

    expect(TestBed.inject(SessionService).hasRole(['cliente'])).toBeTrue();
    expect(TestBed.inject(RegistroDraft).alta()).toBeNull();
    expect(navigate).toHaveBeenCalledOnceWith(CUSTOMER_LOGIN.home);
  });

  it('does not open the session when the BFF records no consent', () => {
    accept();
    submit();

    http
      .expectOne('/web/registro')
      .flush({ ...fakeTokenPair('cliente'), cliente: ALTA, consentimiento: null });
    fixture.detectChanges();

    expect(TestBed.inject(SessionService).isActive()).toBeFalse();
    expect(element('consentimiento-error')?.textContent).toContain('No pudimos crear tu cuenta');
    expect(TestBed.inject(RegistroDraft).alta()).toEqual(ALTA);
    expect(navigate).not.toHaveBeenCalled();
  });

  it('keeps the data for a retry when the BFF fails', () => {
    accept();
    submit();

    http.expectOne('/web/registro').flush(null, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();

    expect(element('consentimiento')?.getAttribute('data-status')).toBe('error');
    expect(TestBed.inject(RegistroDraft).alta()).toEqual(ALTA);
  });

  it('drops the sign-up when the customer declines', () => {
    element('consentimiento-decline')!.click();

    http.expectNone(() => true);
    expect(TestBed.inject(RegistroDraft).alta()).toBeNull();
    expect(navigate).toHaveBeenCalledOnceWith('/login');
  });
});
