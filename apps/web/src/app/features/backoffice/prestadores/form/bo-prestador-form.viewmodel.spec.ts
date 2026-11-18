import { HttpErrorResponse } from '@angular/common/http';
import { Observable, of, Subject, throwError } from 'rxjs';
import { CiudadMapa } from '../../../prestadores/prestadores.gateway';
import { CIUDADES_CO, CIUDADES_MX } from '../../../prestadores/prestadores.testing';
import { Pais } from '../../../prestadores/tipo-prestador';
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
  pais: 'CO',
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
  const rechazo = (codigo: string) =>
    new HttpErrorResponse({ status: 422, error: { codigo, mensaje: 'Rechazado' } });

  it('maps the 422 body codigo and ignores anything else', () => {
    expect(codigoPrestador(new Error('x'))).toBeNull();
    expect(codigoPrestador(new HttpErrorResponse({ status: 500 }))).toBeNull();
    expect(codigoPrestador(new HttpErrorResponse({ status: 422, error: null }))).toBeNull();
    expect(
      codigoPrestador(new HttpErrorResponse({ status: 422, error: { detail: 'ramo_desconocido' } })),
    ).toBeNull();
    expect(codigoPrestador(rechazo('otro'))).toBeNull();
    for (const codigo of [
      'prestador_sin_ramo',
      'ramo_desconocido',
      'coordenada_fuera_de_rango',
      'ciudad_desconocida',
      'pais_desconocido',
    ]) {
      expect(codigoPrestador(rechazo(codigo))).toBe(codigo as never);
    }
  });
});

describe('BoPrestadorFormViewModel', () => {
  function crear(id: string | null = null) {
    const guardados: { entrada: PrestadorEntrada; id: string | null }[] = [];
    const paises: Pais[] = [];
    let ciudades: (pais: Pais) => Observable<CiudadMapa[]> = (pais) =>
      of(pais === 'MX' ? CIUDADES_MX : CIUDADES_CO);
    let obtener = of<PrestadorOperador | null>(FILA);
    let guardar = of(FILA);
    const vm = new BoPrestadorFormViewModel(
      {
        obtener: () => obtener,
        ciudades: (pais) => {
          paises.push(pais);
          return ciudades(pais);
        },
        guardar: (entrada, prestadorId) => {
          guardados.push({ entrada, id: prestadorId });
          return guardar;
        },
      },
      id,
      'CO',
    );
    return {
      vm,
      guardados,
      paises,
      usarCiudades: (fuente: (pais: Pais) => Observable<CiudadMapa[]>) => {
        ciudades = fuente;
      },
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
      new HttpErrorResponse({ status: 422, error: { codigo: 'coordenada_fuera_de_rango' } }),
    );
    vm.guardar();
    expect(vm.errorCodigo()).toBe('coordenada_fuera_de_rango');
    expect(vm.guardado()).toBeFalse();
    expect(guardados[0].entrada).toEqual(
      jasmine.objectContaining({ lat: 4.71, lng: -74.04, tipo: 'taller-motos', pais: 'CO' }),
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
    expect(cargado.vm.pais()).toBe('CO');
    expect(cargado.paises).toEqual(['CO']);
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

  it('changing the country clears the city and reloads its catalog', () => {
    const { vm, paises } = crear();
    vm.cargar();
    expect(vm.ciudades()).toEqual(CIUDADES_CO);
    vm.elegirCiudad('Medellín');
    expect(vm.ciudad()).toBe('Medellín');

    vm.elegirPais('MX');

    expect(vm.pais()).toBe('MX');
    expect(vm.ciudad()).toBe('');
    expect(paises).toEqual(['CO', 'MX']);
    expect(vm.ciudades().map((ciudad) => ciudad.nombre)).toEqual([
      'Ciudad de México',
      'Guadalajara',
      'Monterrey',
    ]);
  });

  it('choosing a city moves the pin and the map to its center and zoom', () => {
    const { vm, guardados } = crear();
    vm.cargar();
    vm.elegirPais('MX');
    vm.elegirCiudad('Ciudad de México');
    expect(vm.ciudad()).toBe('Ciudad de México');
    expect(vm.pin()).toEqual({ lat: 19.4326, lng: -99.1332 });
    expect(vm.objetivo()).toEqual({ lat: 19.4326, lng: -99.1332, zoom: 11 });

    vm.elegirCiudad('Atlantis');
    expect(vm.ciudad()).toBe('Atlantis');
    expect(vm.pin()).toEqual({ lat: 19.4326, lng: -99.1332 });

    vm.nombre.set('Grúa Roma');
    vm.barrio.set('Roma Norte');
    vm.tipo.set('grua');
    vm.telefono.set('55 5555 0101');
    vm.direccion.set('Av. Álvaro Obregón 100');
    vm.horario.set('24 h');
    vm.elegirCiudad('Ciudad de México');
    vm.alternarRamo('viaje');
    vm.guardar();
    expect(guardados[0].entrada).toEqual(
      jasmine.objectContaining({ pais: 'MX', ciudad: 'Ciudad de México', lat: 19.4326 }),
    );
  });

  it('waits at the first city until a coordinate exists, and anchors the pin there', () => {
    const { vm, usarCiudades } = crear();
    usarCiudades(() => throwError(() => new Error('caido')));
    vm.cargar();
    expect(vm.ciudades()).toEqual([]);
    expect(vm.pin()).toBeNull();
    vm.anclarPin();
    expect(vm.lat()).toBeNull();

    usarCiudades(() => of(CIUDADES_CO));
    vm.elegirPais('CO');
    vm.fijarLat('4.7');
    expect(vm.pin()).toEqual({ lat: 4.6097, lng: -74.0817 });
    vm.fijarLat('');
    vm.anclarPin();
    expect(vm.lat()).toBe(4.6097);
    expect(vm.pin()).toEqual({ lat: 4.6097, lng: -74.0817 });

    vm.fijarPin(4.7, -74.03);
    vm.anclarPin();
    expect(vm.pin()).toEqual({ lat: 4.7, lng: -74.03 });
  });

  it('ignores a city catalog that arrives after another country was picked', () => {
    const { vm, usarCiudades } = crear();
    const lento = new Subject<CiudadMapa[]>();
    usarCiudades((pais) => (pais === 'CL' ? lento : of(CIUDADES_MX)));
    vm.elegirPais('CL');
    vm.elegirPais('MX');
    lento.next(CIUDADES_CO);
    expect(vm.ciudades()).toEqual(CIUDADES_MX);
  });
});
