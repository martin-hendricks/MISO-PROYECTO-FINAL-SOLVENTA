import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { authInterceptor } from './auth.interceptor';
import { SessionService } from './session.service';

describe('authInterceptor', () => {
  function setup(token: string | null) {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: SessionService, useValue: { accessToken: () => token } },
      ],
    });
    return {
      client: TestBed.inject(HttpClient),
      http: TestBed.inject(HttpTestingController),
    };
  }

  it('sends the access token to the BFF', () => {
    const { client, http } = setup('jwt');

    client.get('/web/cliente/inicio').subscribe();

    const request = http.expectOne('/web/cliente/inicio');
    expect(request.request.headers.get('Authorization')).toBe('Bearer jwt');
  });

  it('leaves the request alone without a session', () => {
    const { client, http } = setup(null);

    client.get('/web/cliente/inicio').subscribe();

    expect(http.expectOne('/web/cliente/inicio').request.headers.has('Authorization')).toBeFalse();
  });

  it('never sends the token outside the BFF', () => {
    const { client, http } = setup('jwt');

    client.get('https://example.com/data').subscribe();

    expect(
      http.expectOne('https://example.com/data').request.headers.has('Authorization'),
    ).toBeFalse();
  });
});
