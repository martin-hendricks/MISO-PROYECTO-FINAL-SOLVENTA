import { fakeAsync, tick } from '@angular/core/testing';
import { Observable, of, Subject, throwError } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { Catalogo } from '../cotizacion/cotizacion.gateway';
import { Credito, OfertaHipotecaria } from './vida-crediticia.gateway';
import { ETAPAS, VidaCrediticiaViewModel } from './vida-crediticia.viewmodel';

const CATALOGO = {
  ramo: 'Vida hipotecario',
  moneda: 'COP',
  coberturas: [],
  datosRiesgo: [
    { nombre: 'valor', tipo: 'rango', minimo: '1000000', maximo: '500000000' },
    { nombre: 'plazoMeses', tipo: 'rango', minimo: '6', maximo: '360' },
  ],
} as unknown as Catalogo;

const OFERTA = { cotizacionId: 'COT-1', prima: 140100 } as unknown as OfertaHipotecaria;

function listo(source: (credito: Credito) => Observable<OfertaHipotecaria>, etapaMs = 700) {
  const vm = new VidaCrediticiaViewModel(() => of(CATALOGO), source, etapaMs);
  vm.loadCatalog();
  vm.prefill({ valor: 180000000, plazoMeses: 240 });
  return vm;
}

describe('VidaCrediticiaViewModel', () => {
  it('advances one profiling step at a time and shows the offer only after the last one', fakeAsync(() => {
    const vm = listo(() => of(OFERTA));

    vm.authorize();
    expect(vm.status()).toBe('requesting');
    expect(ETAPAS.map((etapa) => vm.estadoEtapa(etapa))).toEqual(['active', 'pending', 'pending', 'pending']);

    tick(700);
    expect(ETAPAS.map((etapa) => vm.estadoEtapa(etapa))).toEqual(['done', 'active', 'pending', 'pending']);

    tick(1400);
    expect(ETAPAS.map((etapa) => vm.estadoEtapa(etapa))).toEqual(['done', 'done', 'done', 'active']);
    expect(vm.oferta()).toBeNull();

    tick(700);
    expect(vm.status()).toBe('offer');
    expect(vm.oferta()).toBe(OFERTA);
    expect(ETAPAS.map((etapa) => vm.estadoEtapa(etapa))).toEqual(['done', 'done', 'done', 'done']);
  }));

  it('waits for a slow core after the steps end', fakeAsync(() => {
    const respuesta = new Subject<OfertaHipotecaria>();
    const vm = listo(() => respuesta);

    vm.authorize();
    tick(2800);
    expect(vm.status()).toBe('requesting');

    respuesta.next(OFERTA);
    respuesta.complete();
    expect(vm.status()).toBe('offer');
  }));

  it('stops the steps when the core fails', fakeAsync(() => {
    const vm = listo(() => throwError(() => new HttpErrorResponse({ status: 503 })));

    vm.authorize();
    tick(2800);

    expect(vm.status()).toBe('error');
    expect(vm.estadoEtapa('openFinance')).toBe('active');
  }));

  it('does not authorize without valid mortgage data', () => {
    const vm = new VidaCrediticiaViewModel(() => of(CATALOGO), () => of(OFERTA), 0);
    vm.loadCatalog();

    vm.authorize();

    expect(vm.status()).toBe('consent');
  });
});
