import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { BILLETERA } from './billetera.testing';
import { BilleteraGateway } from './billetera.gateway';

describe('BilleteraGateway', () => {
  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return {
      gateway: TestBed.inject(BilleteraGateway),
      http: TestBed.inject(HttpTestingController),
    };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('lists deposits and maps a missing deposit to null', async () => {
    const { gateway, http } = setup();
    const pending = firstValueFrom(gateway.detail('abc'));
    http
      .expectOne('/web/cliente/billetera/abc')
      .flush({}, { status: 404, statusText: 'Not Found' });
    expect(await pending).toBeNull();

    const lista = firstValueFrom(gateway.list());
    http.expectOne('/web/cliente/billetera').flush(BILLETERA);
    expect((await lista).totalRecibido).toBe(1070000);
    expect((await lista).movimientos[0].monto).toBe(890000);
    expect((await lista).movimientos[1].monto).toBe(180000);
  });

  it('rethrows errors other than not found', async () => {
    const { gateway, http } = setup();
    const pending = firstValueFrom(gateway.detail('abc'));
    http.expectOne('/web/cliente/billetera/abc').flush({}, { status: 503, statusText: 'Down' });
    await expectAsync(pending).toBeRejectedWith(jasmine.any(HttpErrorResponse));
  });
});
