import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter, Router } from '@angular/router';
import { SessionService } from '../../../core/session/session.service';
import { soloOperadorPrestadores } from './bo-prestadores.guard';

describe('soloOperadorPrestadores', () => {
  function activar(role: 'operador' | 'asesor') {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: SessionService, useValue: { role: signal(role) } },
      ],
    });
    return TestBed.runInInjectionContext(() => soloOperadorPrestadores({} as never, {} as never));
  }

  it('allows the operador and sends the asesor back to the list', () => {
    expect(activar('operador')).toBeTrue();
    TestBed.resetTestingModule();
    const destino = activar('asesor');
    expect(destino).toEqual(TestBed.inject(Router).parseUrl('/cms/prestadores'));
  });
});
