import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';
import { PrestadorEntrada, PrestadorOperador } from '../bo-prestadores.gateway';
import {
  BoPrestadorFormViewModel,
  codigoPrestador,
} from './bo-prestador-form.viewmodel';

const FILA: PrestadorOperador = {
  id: 'PRE-BOG-06',
  nombre: 'Taller Moto Chapinero',
  tipo: 'taller-motos',
  ramos: ['soat-motocicleta'],
  direccion: 'Cra 13',
  ciudad: 'Bogotá',
  barrio: 'Chapinero',
  lat: 4.6355,
  lng: -74.0655,
  telefono: '601 555 0112',
  horario: 'Lun–Sáb 7:00–19:00',
  estado: 'activo',
  actualizadoEn: '2026-11-17T00:00:00Z',
};

describe('codigoPrestador', () => {
  it('maps the three 422 codes and ignores anything else', () => {
    expect(codigoPrestador(new Error('x'))).toBeNull();
    expect(codigoPrestador(new HttpErrorResponse({ status: 500 }))).toBeNull();
    expect(
      codigoPrestador(new HttpErrorResponse({ status: 422, error: { detail: 'otro' } })),
    ).toBeNull();
    expect(
      codigoPrestador(
        new HttpErrorResponse({ status: 422, error: { detail: 'prestador_sin_ramo' } }),
      ),
    ).toBe('prestador_sin_ramo');
    expect(
      codigoPrestador(
        new HttpErrorResponse({ status: 422, error: { detail: 'ramo_desconocido' } }),
      ),
    ).toBe('ramo_desconocido');
    expect(
      codigoPrestador(
        new HttpErrorResponse({ status: 422, error: { detail: 'coordenada_fuera_de_rango' } }),
      ),
    ).toBe('coordenada_fuera_de_rango');
  });
});

describe('BoPrestadorFormViewModel', () => {
  function crear(id: string | null = null) {
    const guardados: { entrada: PrestadorEntrada; id: string | null }[] = [];
    let obtener = of<PrestadorOperador | null>(FILA);
    let guardar = of(FILA);
    const vm = new BoPrestadorFormViewModel(
      {
        obtener: () => obtener,
        guardar: (entrada, prestadorId) => {
          guardados.push({ entrada, id: prestadorId });
          return guardar;
        },
      },
      id,
    );
    return {
      vm,
      guardados,
      sinFila: () => {
        obtener = of(null);
      },
      fallarLectura: () => {
        obtener = throwError(() => new Error('caido'));
      },
      fallarGuardado: (error: unknown) => {
        guardar = throwError(() => error);
      },
    };
  }

  function completar(vm: BoPrestadorFormViewModel): void {
    vm.nombre.set('Taller Moto Norte Usaquén');
    vm.barrio.set('Usaquén');
    vm.tipo.set('taller-motos');
    vm.telefono.set('601 555 0199');
    vm.direccion.set('Cra 7 #120-10');
    vm.horario.set('Lun–Vie 8:00–18:00');
    vm.ciudad.set('Bogotá');
    vm.alternarRamo('soat-motocicleta');
    vm.fijarPin(4.7, -74.03);
  }

  it('hides the ramo error until the first save, then refuses to send', () => {
    const { vm, guardados } = crear();
    vm.cargar();
    expect(vm.errorRamo()).toBeFalse();
    expect(vm.status()).toBe('ready');

    vm.guardar();
    expect(vm.errorRamo()).toBeTrue();
    expect(guardados).toEqual([]);

    vm.nombre.set('Solo el nombre');
    vm.guardar();
    expect(guardados).toEqual([]);
    vm.barrio.set('Barrio');
    vm.guardar();
    vm.tipo.set('grua');
    vm.guardar();
    vm.telefono.set('1');
    vm.guardar();
    vm.direccion.set('Calle 1');
    vm.guardar();
    vm.horario.set('Lun');
    vm.guardar();
    vm.ciudad.set('Bogotá');
    vm.guardar();
    vm.alternarRamo('viaje');
    expect(vm.errorRamo()).toBeFalse();
    vm.guardar();
    vm.fijarLat('4,2');
    vm.fijarLat('');
    vm.fijarLat('4.7');
    vm.guardar();
    vm.fijarLng('no');
    vm.fijarLng('-74.03');
    vm.guardar();
    expect(guardados.length).toBe(1);
    expect(guardados[0].entrada.lat).toBe(4.7);
    expect(guardados[0].entrada.lng).toBe(-74.03);
    expect(guardados[0].entrada.ramos).toEqual(['viaje']);
    expect(vm.guardado()).toBeTrue();

    vm.alternarRamo('viaje');
    vm.alternarRamo('pagos');
    expect(vm.ramos()).toEqual(['pagos']);
  });

  it('reads lat and lng from the pin and maps 422 codes', () => {
    const { vm, guardados, fallarGuardado } = crear();
    completar(vm);
    vm.fijarPin(4.71, -74.04);
    fallarGuardado(
      new HttpErrorResponse({ status: 422, error: { detail: 'coordenada_fuera_de_rango' } }),
    );
    vm.guardar();
    expect(vm.errorCodigo()).toBe('coordenada_fuera_de_rango');
    expect(vm.guardado()).toBeFalse();
    expect(guardados[0].entrada).toEqual(
      jasmine.objectContaining({ lat: 4.71, lng: -74.04, tipo: 'taller-motos' }),
    );

    const generico = crear();
    completar(generico.vm);
    generico.fallarGuardado(new Error('red'));
    generico.vm.guardar();
    expect(generico.vm.errorCodigo()).toBe('generico');
  });

  it('loads an existing provider and reports a missing or failed read', () => {
    const cargado = crear('PRE-BOG-06');
    cargado.vm.cargar();
    expect(cargado.vm.nombre()).toBe('Taller Moto Chapinero');
    expect(cargado.vm.lat()).toBe(4.6355);
    expect(cargado.vm.status()).toBe('ready');

    const falta = crear('nope');
    falta.sinFila();
    falta.vm.cargar();
    expect(falta.vm.status()).toBe('not-found');

    const caido = crear('x');
    caido.fallarLectura();
    caido.vm.cargar();
    expect(caido.vm.status()).toBe('error');
  });
});
