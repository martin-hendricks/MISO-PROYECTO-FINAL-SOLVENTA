import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { Observable, of, throwError } from 'rxjs';
import { authInterceptor } from './auth.interceptor';
import { SessionService } from './session.service';

describe('authInterceptor', () => {
  function setup(
    options: {
      token?: string | null;
      refresh?: () => Observable<void>;
    } = {},
  ) {
    const state = { token: options.token === undefined ? 'jwt' : options.token };
    const refresh = jasmine
      .createSpy('refresh')
      .and.callFake(options.refresh ?? (() => of(undefined)));
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        {
          provide: SessionService,
          useValue: { accessToken: () => state.token, refresh },
        },
      ],
    });
    return {
      client: TestBed.inject(HttpClient),
      http: TestBed.inject(HttpTestingController),
      router: TestBed.inject(Router),
      refresh,
      setToken: (token: string | null) => {
        state.token = token;
      },
    };
  }

  it('sends the access token to the BFF', () => {
    const { client, http } = setup();

    client.get('/web/cliente/inicio').subscribe();

    const request = http.expectOne('/web/cliente/inicio');
    expect(request.request.headers.get('Authorization')).toBe('Bearer jwt');
  });

  it('leaves the request alone without a session', () => {
    const { client, http } = setup({ token: null });

    client.get('/web/cliente/inicio').subscribe();

    expect(http.expectOne('/web/cliente/inicio').request.headers.has('Authorization')).toBeFalse();
  });

  it('never sends the token outside the BFF', () => {
    const { client, http } = setup();

    client.get('https://example.com/data').subscribe();

    expect(
      http.expectOne('https://example.com/data').request.headers.has('Authorization'),
    ).toBeFalse();
  });

  it('refreshes once and retries a BFF 401 with the new access token', () => {
    const { client, http, refresh, setToken } = setup({
      token: 'old',
      refresh: () => {
        setToken('new');
        return of(undefined);
      },
    });
    let failed = false;

    client.get('/web/cliente/inicio').subscribe({ error: () => (failed = true) });
    const first = http.expectOne('/web/cliente/inicio');
    expect(first.request.headers.get('Authorization')).toBe('Bearer old');
    first.flush(null, { status: 401, statusText: 'Unauthorized' });

    expect(refresh).toHaveBeenCalledTimes(1);
    const retry = http.expectOne('/web/cliente/inicio');
    expect(retry.request.headers.get('Authorization')).toBe('Bearer new');
    expect(retry.request.headers.get('X-Auth-Retry')).toBe('1');
    retry.flush({ ok: true });

    expect(failed).toBeFalse();
  });

  it('does not refresh again when the retried request is still unauthorized', () => {
    const { client, http, refresh, router } = setup({
      token: 'old',
      refresh: () => of(undefined),
    });
    const navigate = spyOn(router, 'navigateByUrl');
    let failed = false;

    client.get('/web/cliente/inicio').subscribe({ error: () => (failed = true) });
    http.expectOne('/web/cliente/inicio').flush(null, { status: 401, statusText: 'Unauthorized' });
    http.expectOne('/web/cliente/inicio').flush(null, { status: 401, statusText: 'Unauthorized' });

    expect(refresh).toHaveBeenCalledTimes(1);
    expect(navigate).not.toHaveBeenCalled();
    expect(failed).toBeTrue();
  });

  for (const url of ['/web/sesion/ingreso', '/web/sesion/refresh', '/web/sesion/salida']) {
    it(`does not refresh a 401 from ${url}`, () => {
      const { client, http, refresh } = setup();
      let failed = false;

      client.post(url, {}).subscribe({ error: () => (failed = true) });
      http.expectOne(url).flush(null, { status: 401, statusText: 'Unauthorized' });

      expect(refresh).not.toHaveBeenCalled();
      expect(failed).toBeTrue();
    });
  }

  it('sends the customer to login when refresh fails', () => {
    const { client, http, router } = setup({
      refresh: () => throwError(() => new Error('rejected')),
    });
    const navigate = spyOn(router, 'navigateByUrl').and.resolveTo(true);
    let failed = false;

    client.get('/web/cliente/inicio').subscribe({ error: () => (failed = true) });
    http.expectOne('/web/cliente/inicio').flush(null, { status: 401, statusText: 'Unauthorized' });

    expect(navigate).toHaveBeenCalledOnceWith('/login');
    expect(failed).toBeTrue();
    http.expectNone('/web/cliente/inicio');
  });

  it('sends the back office to its login when refresh fails there', () => {
    const { client, http, router } = setup({
      refresh: () => throwError(() => new Error('rejected')),
    });
    spyOnProperty(router, 'url', 'get').and.returnValue('/cms/clientes');
    const navigate = spyOn(router, 'navigateByUrl').and.resolveTo(true);

    client.get('/web/asesor/clientes').subscribe({ error: () => undefined });
    http.expectOne('/web/asesor/clientes').flush(null, { status: 401, statusText: 'Unauthorized' });

    expect(navigate).toHaveBeenCalledOnceWith('/cms/login');
  });
});
