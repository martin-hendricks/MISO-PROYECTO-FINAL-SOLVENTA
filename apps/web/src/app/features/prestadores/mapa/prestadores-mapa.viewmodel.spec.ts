import { of, Subject, throwError } from 'rxjs';
import { GeolocationPort, Posicion } from '../geolocation-port';
import {
  BusquedaPrestadores,
  BusquedaSiniestro,
  ConsultaPrestadores,
} from '../prestadores.gateway';
import { BUSQUEDA, BUSQUEDA_SINIESTRO, PRESTADOR } from '../prestadores.testing';
import {
  esBloqueoUbicacion,
  PrestadoresMapaViewModel,
  PuertosPrestadores,
} from './prestadores-mapa.viewmodel';

describe('esBloqueoUbicacion', () => {
  it('treats permission, unavailable and timeout as a blocked position', () => {
    expect(esBloqueoUbicacion({ code: 1 })).toBeTrue();
    expect(esBloqueoUbicacion({ code: 2 })).toBeTrue();
    expect(esBloqueoUbicacion({ code: 3 })).toBeTrue();
    expect(esBloqueoUbicacion({ code: 9 })).toBeFalse();
    expect(esBloqueoUbicacion(null)).toBeFalse();
    expect(esBloqueoUbicacion(4)).toBeFalse();
    expect(esBloqueoUbicacion({})).toBeFalse();
  });
});

describe('PrestadoresMapaViewModel', () => {
  function crear(
    geo: GeolocationPort,
    claimId: string | null = null,
    puertos?: Partial<PuertosPrestadores>,
  ) {
    const consultas: ConsultaPrestadores[] = [];
    const completos = {
      cercanos: (consulta: ConsultaPrestadores) => {
        consultas.push(consulta);
        return of(BUSQUEDA);
      },
      porSiniestro: () => of(BUSQUEDA_SINIESTRO),
      ...puertos,
    };
    if (puertos?.cercanos) {
      completos.cercanos = (consulta) => {
        consultas.push(consulta);
        return puertos.cercanos!(consulta);
      };
    }
    return {
      vm: new PrestadoresMapaViewModel(completos, geo, claimId),
      consultas,
    };
  }

  function concedida(pos: Posicion = { lat: 4.6432, lng: -74.0631 }): GeolocationPort {
    return { actual: () => Promise.resolve(pos) };
  }

  it('queries near me when geolocation is granted, and again when a chip changes', async () => {
    const { vm, consultas } = crear(concedida());
    vm.cargar();
    expect(vm.status()).toBe('loading');
    await Promise.resolve();

    expect(vm.modo()).toBe('nearMe');
    expect(vm.diceCercaDeTi()).toBeTrue();
    expect(vm.muestraDistancias()).toBeTrue();
    expect(vm.referenciaDistancia()).toBe('posicion');
    expect(vm.ramoBloqueado()).toBeFalse();
    expect(consultas[0]).toEqual({ lat: 4.6432, lng: -74.0631, ramo: null, radioKm: 10 });
    expect(vm.prestadores()[0].id).toBe('PRE-BOG-06');
    expect(vm.km(PRESTADOR)).toBe('0,9');
    expect(vm.km({ ...PRESTADOR, distanciaKm: null })).toBeNull();
    expect(vm.comoLlegar(PRESTADOR)).toBe(
      'https://www.google.com/maps/dir/?api=1&destination=4.6355,-74.0655',
    );
    vm.abrir(PRESTADOR.id);
    vm.abrir(PRESTADOR.id);
    expect(vm.abiertoId()).toBeNull();

    vm.seleccionarRamo('soat-motocicleta');
    vm.seleccionarRamo(null);
    expect(consultas.map((consulta) => consulta.ramo)).toEqual([
      null,
      'soat-motocicleta',
      null,
    ]);
    expect(vm.ramo()).toBeNull();
  });

  it('keeps the list when the map is unavailable', async () => {
    const { vm } = crear(concedida());
    vm.fijarMapa('no-disponible');
    vm.cargar();
    await Promise.resolve();
    expect(vm.mapa()).toBe('no-disponible');
    expect(vm.status()).toBe('ready');
    expect(vm.prestadores().length).toBe(1);
  });

  it('falls back to Bogotá without distances or cerca de ti when location is denied or times out', async () => {
    for (const code of [1, 3]) {
      const { vm, consultas } = crear({ actual: () => Promise.reject({ code }) });
      vm.cargar();
      await Promise.resolve();
      expect(vm.modo()).toBe('chooseCity');
      expect(vm.ciudad()).toBe('Bogotá');
      expect(vm.diceCercaDeTi()).toBeFalse();
      expect(vm.muestraDistancias()).toBeFalse();
      expect(vm.referenciaDistancia()).toBeNull();
      expect(vm.km(PRESTADOR)).toBeNull();
      expect(consultas[0]).toEqual({ ciudad: 'Bogotá', ramo: null });
      expect(vm.status()).toBe('ready');
    }
  });

  it('retries location from Usar mi ubicación and switches a chosen city', async () => {
    let intentos = 0;
    const { vm, consultas } = crear({
      actual: () => {
        intentos += 1;
        return intentos === 1
          ? Promise.reject({ code: 1 })
          : Promise.resolve({ lat: 6.2, lng: -75.5 });
      },
    });
    vm.cargar();
    await Promise.resolve();
    expect(vm.modo()).toBe('chooseCity');

    vm.elegirCiudad('Medellín');
    expect(consultas.at(-1)).toEqual({ ciudad: 'Medellín', ramo: null });

    vm.usarUbicacion();
    await Promise.resolve();
    expect(vm.modo()).toBe('nearMe');
    expect(vm.diceCercaDeTi()).toBeTrue();
    expect(consultas.at(-1)).toEqual({ lat: 6.2, lng: -75.5, ramo: null, radioKm: 10 });
  });

  it('shows a retry when the read fails, including a position that is not a denial', async () => {
    const caido = crear(concedida(), null, {
      cercanos: () => throwError(() => new Error('caido')),
    });
    caido.vm.cargar();
    await Promise.resolve();
    expect(caido.vm.status()).toBe('error');
    expect(caido.vm.prestadores()).toEqual([]);

    const raro = crear({ actual: () => Promise.reject(new Error('sensor')) });
    raro.vm.cargar();
    await Promise.resolve();
    expect(raro.vm.status()).toBe('error');
  });

  it('ignores a stale geolocation result', async () => {
    function diferida() {
      const resolvers: ((pos: Posicion) => void)[] = [];
      const rejecters: ((error: unknown) => void)[] = [];
      const geo: GeolocationPort = {
        actual: () =>
          new Promise((resolve, reject) => {
            resolvers.push(resolve);
            rejecters.push(reject);
          }),
      };
      return { ...crear(geo), resolvers, rejecters };
    }

    const exito = diferida();
    exito.vm.cargar();
    exito.vm.usarUbicacion();
    exito.resolvers[0]({ lat: 1, lng: 1 });
    exito.resolvers[1]({ lat: 4.6, lng: -74.1 });
    await Promise.resolve();
    expect(exito.consultas).toEqual([{ lat: 4.6, lng: -74.1, ramo: null, radioKm: 10 }]);

    const denegada = diferida();
    denegada.vm.cargar();
    denegada.vm.usarUbicacion();
    denegada.rejecters[0]({ code: 1 });
    denegada.resolvers[1]({ lat: 4.6, lng: -74.1 });
    await Promise.resolve();
    expect(denegada.vm.modo()).toBe('nearMe');
    expect(denegada.consultas).toEqual([{ lat: 4.6, lng: -74.1, ramo: null, radioKm: 10 }]);
  });

  it('ignores a stale list response and shows empty when the latest read has no rows', async () => {
    const streams: Subject<BusquedaPrestadores>[] = [];
    const { vm } = crear(concedida(), null, {
      cercanos: () => {
        const stream = new Subject<BusquedaPrestadores>();
        streams.push(stream);
        return stream;
      },
    });
    vm.cargar();
    await Promise.resolve();
    vm.seleccionarRamo('viaje');
    streams[0].next(BUSQUEDA);
    streams[0].error(new Error('tarde'));
    expect(vm.status()).toBe('loading');
    streams[1].next({ ...BUSQUEDA, prestadores: [] });
    expect(vm.status()).toBe('empty');
    expect(vm.prestadores()).toEqual([]);
  });

  it('locks the claim chip, titles the claim and labels distances from the event', () => {
    const { vm, consultas } = crear(concedida(), 'sin-1988');
    vm.cargar();
    expect(vm.modo()).toBe('claim');
    expect(vm.ramoBloqueado()).toBeTrue();
    expect(vm.siniestro()?.numero).toBe('SIN-1988');
    expect(vm.ramo()).toBe('soat-motocicleta');
    expect(vm.referenciaDistancia()).toBe('evento');
    expect(vm.km(vm.prestadores()[0])).toBe('0,8');
    expect(vm.diceCercaDeTi()).toBeFalse();
    vm.seleccionarRamo('pagos');
    vm.seleccionarRamo(null);
    expect(vm.ramo()).toBe('soat-motocicleta');
    expect(consultas).toEqual([]);
  });

  it('offers near me when the claim has no geotag, and treats a missing center the same way', async () => {
    const sinGeo = crear(concedida(), 'sin-1', {
      porSiniestro: () =>
        of({
          ...BUSQUEDA_SINIESTRO,
          sinGeoetiqueta: true,
          prestadores: [],
        }),
    });
    sinGeo.vm.cargar();
    expect(sinGeo.vm.status()).toBe('sin-geo');
    expect(sinGeo.vm.modo()).toBe('claim');
    sinGeo.vm.usarUbicacion();
    await Promise.resolve();
    expect(sinGeo.vm.modo()).toBe('nearMe');
    expect(sinGeo.vm.diceCercaDeTi()).toBeTrue();
    expect(sinGeo.consultas[0].lat).toBe(4.6432);

    const sinCentro = crear(concedida(), 'sin-2', {
      porSiniestro: () => of({ ...BUSQUEDA_SINIESTRO, sinGeoetiqueta: false, centro: null }),
    });
    sinCentro.vm.cargar();
    expect(sinCentro.vm.status()).toBe('sin-geo');
  });

  it('shows not-found, an empty claim list, and a retry when the claim read fails', () => {
    const ajeno = crear(concedida(), 'ajeno', { porSiniestro: () => of(null) });
    ajeno.vm.cargar();
    expect(ajeno.vm.status()).toBe('not-found');
    expect(ajeno.vm.prestadores()).toEqual([]);

    const vacio = crear(concedida(), 'vacio', {
      porSiniestro: () => of({ ...BUSQUEDA_SINIESTRO, prestadores: [] }),
    });
    vacio.vm.cargar();
    expect(vacio.vm.status()).toBe('empty');

    const caido = crear(concedida(), 'caido', {
      porSiniestro: () => throwError(() => new Error('caido')),
    });
    caido.vm.cargar();
    expect(caido.vm.status()).toBe('error');
  });

  it('ignores a stale claim response after the customer asks for their location', async () => {
    const stream = new Subject<BusquedaSiniestro | null>();
    let resolvers: ((pos: Posicion) => void)[] = [];
    const { vm } = crear(
      {
        actual: () => new Promise((resolve) => resolvers.push(resolve)),
      },
      'sin-1988',
      { porSiniestro: () => stream },
    );
    vm.cargar();
    vm.usarUbicacion();
    stream.next(BUSQUEDA_SINIESTRO);
    stream.error(new Error('tarde'));
    expect(vm.siniestro()).toBeNull();
    expect(vm.status()).toBe('loading');
    resolvers[0]({ lat: 4, lng: -74 });
    await Promise.resolve();
    expect(vm.modo()).toBe('nearMe');
    expect(vm.status()).toBe('ready');
  });
});
