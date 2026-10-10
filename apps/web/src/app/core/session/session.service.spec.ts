import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { SESSION_STORAGE_KEY, SessionService } from './session.service';
import { fakeTokenPair } from './session.testing';

describe('SessionService', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return {
      session: TestBed.inject(SessionService),
      http: TestBed.inject(HttpTestingController),
    };
  }

  beforeEach(() => sessionStorage.removeItem(SESSION_STORAGE_KEY));
  afterEach(() => sessionStorage.removeItem(SESSION_STORAGE_KEY));

  it('starts without a session', () => {
    const { session } = setup();

    expect(session.isActive()).toBeFalse();
    expect(session.accessToken()).toBeNull();
    expect(session.role()).toBeNull();
  });

  it('keeps the token pair and reads the role from the token', () => {
    const { session, http } = setup();
    const pair = fakeTokenPair('asesor');
    let done = false;

    session
      .signIn({ email: 'asesor@solventa.com', password: 'secreto', role: 'asesor' })
      .subscribe(() => (done = true));
    const request = http.expectOne('/web/sesion/ingreso');
    request.flush(pair);

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      correo: 'asesor@solventa.com',
      contrasena: 'secreto',
      rol: 'asesor',
    });
    expect(done).toBeTrue();
    expect(session.isActive()).toBeTrue();
    expect(session.accessToken()).toBe(pair.accessToken);
    expect(session.role()).toBe('asesor');
    expect(session.subject()).toBe('camila@correo.com');
    expect(session.hasRole(['asesor', 'operador'])).toBeTrue();
    expect(session.hasRole(['cliente'])).toBeFalse();
    expect(sessionStorage.getItem(SESSION_STORAGE_KEY)).toBe(JSON.stringify(pair));
  });

  it('leaves the role out when the BFF assigns it', () => {
    const { session, http } = setup();

    session.signIn({ email: 'camila.restrepo@solventa.co', password: 'secreto' }).subscribe();
    const request = http.expectOne('/web/sesion/ingreso');
    request.flush(fakeTokenPair('asesor'));

    expect(request.request.body).toEqual({
      correo: 'camila.restrepo@solventa.co',
      contrasena: 'secreto',
    });
  });

  it('fails when the answer has no readable token', () => {
    const { session, http } = setup();
    let failed = false;

    session
      .signIn({ email: 'c@correo.com', password: 'secreto', role: 'cliente' })
      .subscribe({ error: () => (failed = true) });
    http.expectOne('/web/sesion/ingreso').flush({ accessToken: 'no-es-jwt' });

    expect(failed).toBeTrue();
    expect(session.isActive()).toBeFalse();
  });

  it('restores the session kept in the tab', () => {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(fakeTokenPair()));

    const { session } = setup();

    expect(session.isActive()).toBeTrue();
    expect(session.role()).toBe('cliente');
  });

  it('does not treat an expired token as a session', () => {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(fakeTokenPair('cliente', -1)));

    const { session } = setup();

    expect(session.isActive()).toBeFalse();
  });

  it('ignores a corrupt stored session', () => {
    sessionStorage.setItem(SESSION_STORAGE_KEY, '{');

    const { session } = setup();

    expect(session.isActive()).toBeFalse();
  });

  it('forgets the session on sign out even if the BFF fails', () => {
    const pair = fakeTokenPair();
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(pair));
    const { session, http } = setup();

    session.signOut();
    const request = http.expectOne('/web/sesion/salida');
    request.flush(null, { status: 500, statusText: 'Server Error' });

    expect(request.request.headers.get('Authorization')).toBe(`Bearer ${pair.accessToken}`);

    expect(session.isActive()).toBeFalse();
    expect(sessionStorage.getItem(SESSION_STORAGE_KEY)).toBeNull();
  });

  it('does not call the BFF on sign out without a session', () => {
    const { session, http } = setup();

    session.signOut();

    http.expectNone('/web/sesion/salida');
    expect(session.isActive()).toBeFalse();
  });
});
