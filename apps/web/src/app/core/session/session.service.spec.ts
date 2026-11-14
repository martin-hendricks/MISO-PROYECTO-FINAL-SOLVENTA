import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { asyncScheduler, Subscription } from 'rxjs';
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

  it('opens the session with a pair issued elsewhere, such as the sign-up', () => {
    const { session } = setup();
    const pair = fakeTokenPair('cliente');

    session.start(pair);

    expect(session.hasRole(['cliente'])).toBeTrue();
    expect(sessionStorage.getItem(SESSION_STORAGE_KEY)).toBe(JSON.stringify(pair));
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

  it('stores one rotated pair when two callers refresh together', () => {
    const { session, http } = setup();
    const current = fakeTokenPair();
    const rotated = fakeTokenPair('asesor');
    session.start(current);
    let firstDone = false;
    let secondDone = false;

    session.refresh().subscribe(() => (firstDone = true));
    session.refresh().subscribe(() => (secondDone = true));
    const request = http.expectOne('/web/sesion/refresh');
    request.flush(rotated);

    expect(request.request.body).toEqual({ refreshToken: current.refreshToken });
    expect(firstDone).toBeTrue();
    expect(secondDone).toBeTrue();
    expect(session.accessToken()).toBe(rotated.accessToken);
    expect(session.role()).toBe('asesor');
    expect(sessionStorage.getItem(SESSION_STORAGE_KEY)).toBe(JSON.stringify(rotated));
    http.expectNone('/web/sesion/refresh');
  });

  it('clears the session when refresh is rejected and does not sign out remotely', () => {
    const { session, http } = setup();
    session.start(fakeTokenPair());
    let failed = false;

    session.refresh().subscribe({ error: () => (failed = true) });
    http.expectOne('/web/sesion/refresh').flush(null, { status: 401, statusText: 'Unauthorized' });

    expect(failed).toBeTrue();
    expect(session.isActive()).toBeFalse();
    expect(sessionStorage.getItem(SESSION_STORAGE_KEY)).toBeNull();
    http.expectNone('/web/sesion/salida');
  });

  it('refreshes a restored session one minute before the access token expires', () => {
    spyOn(Date, 'now').and.returnValue(1_700_000_000_000);
    const scheduled = captureSchedule();
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(fakeTokenPair('cliente', 120)));
    const { session, http } = setup();

    expect(scheduled[0].delay).toBe(60_000);
    http.expectNone('/web/sesion/refresh');
    scheduled[0].run();
    http.expectOne('/web/sesion/refresh').flush(fakeTokenPair('cliente', 900));

    expect(scheduled[1].delay).toBe(840_000);
    session.signOut();
    http.expectOne('/web/sesion/salida').flush({});
  });

  it('does not refresh an access token that is already expired', () => {
    const schedule = spyOn(asyncScheduler, 'schedule');
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(fakeTokenPair('cliente', -1)));
    const { http } = setup();

    expect(schedule).not.toHaveBeenCalled();
    http.expectNone('/web/sesion/refresh');
  });

  it('cancels the scheduled refresh on sign out', () => {
    const scheduled = captureSchedule();
    const { session, http } = setup();
    session.start(fakeTokenPair('cliente', 120));

    session.signOut();
    http.expectOne('/web/sesion/salida').flush({});

    expect(scheduled[0].handle.closed).toBeTrue();
    http.expectNone('/web/sesion/refresh');
  });

  it('logging in as a second user leaves only that session, without mixing tokens or claims', () => {
    const { session, http } = setup();
    const userA = fakeTokenPair('asesor');
    const userB = fakeTokenPair('operador');

    session.start(userA);
    expect(session.accessToken()).toBe(userA.accessToken);
    expect(session.role()).toBe('asesor');

    session.start(userB);

    expect(session.accessToken()).toBe(userB.accessToken);
    expect(session.accessToken()).not.toBe(userA.accessToken);
    expect(session.role()).toBe('operador');
    expect(sessionStorage.getItem(SESSION_STORAGE_KEY)).toBe(JSON.stringify(userB));
    http.expectNone('/web/sesion/refresh');
  });

  it("a stale refresh timer from user A's session cannot land on user B's session", () => {
    const scheduled = captureSchedule();
    const { session, http } = setup();
    const userA = fakeTokenPair('asesor', 120);
    const userB = fakeTokenPair('operador', 300);

    // A inicia sesión: se programa su timer de refresco (sin dejarlo disparar).
    session.start(userA);
    expect(scheduled.length).toBe(1);
    const staleTimerFromA = scheduled[0].handle;
    expect(staleTimerFromA.closed).toBeFalse();

    // A cierra sesión antes de que su timer llegara a ejecutarse.
    session.signOut();
    http.expectOne('/web/sesion/salida').flush({});

    // El cierre de sesión debe cancelar ese timer de inmediato: es la
    // garantía que evita que, si llegara a disparar, pise a quien inicie
    // sesión después.
    expect(staleTimerFromA.closed).toBeTrue();

    // B inicia sesión en el mismo tab/servicio.
    session.start(userB);

    // Solo debe quedar programado el timer de B: el de A sigue cancelado y
    // no se programó ninguno adicional en su nombre.
    expect(scheduled.length).toBe(2);
    expect(staleTimerFromA.closed).toBeTrue();
    const timerFromB = scheduled[1].handle;
    expect(timerFromB.closed).toBeFalse();

    // Ninguna petición de refresh quedó pendiente en este punto: el timer
    // fantasma de A nunca llegó a dispararse.
    http.expectNone('/web/sesion/refresh');

    // El estado de sesión sigue siendo el de B.
    expect(session.accessToken()).toBe(userB.accessToken);
    expect(session.role()).toBe('operador');

    // Si B's propio timer dispara más adelante, rota con el refreshToken de
    // B, nunca con el de A.
    scheduled[1].run();
    const request = http.expectOne('/web/sesion/refresh');
    expect(request.request.body).toEqual({ refreshToken: userB.refreshToken });
    request.flush(fakeTokenPair('operador', 300));
  });
});

function captureSchedule(): Array<{ delay: number; run: () => void; handle: Subscription }> {
  const scheduled: Array<{ delay: number; run: () => void; handle: Subscription }> = [];
  spyOn(asyncScheduler, 'schedule').and.callFake(((work: () => void, delay = 0) => {
    const handle = new Subscription();
    scheduled.push({ delay, run: () => work(), handle });
    return handle;
  }) as typeof asyncScheduler.schedule);
  return scheduled;
}
