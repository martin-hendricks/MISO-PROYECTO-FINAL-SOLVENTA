import { signal } from '@angular/core';
import { Observable, of, Subject, throwError } from 'rxjs';
import type { Locale } from '../../../core/i18n/locale.service';
import { GeolocationPort, Posicion } from '../geolocation-port';
import {
  AreaVisible,
  BusquedaPrestadores,
  BusquedaSiniestro,
  CiudadMapa,
  ConsultaPrestadores,
} from '../prestadores.gateway';
import {
  AREA_CHAPINERO,
  AREA_MEDELLIN,
  BUSQUEDA,
  BUSQUEDA_SINIESTRO,
  CIUDADES_CO,
  CIUDADES_MX,
  IPS,
  PRESTADOR,
} from '../prestadores.testing';
import type { Pais } from '../tipo-prestador';
import {
  esBloqueoUbicacion,
  PrestadoresMapaViewModel,
  PuertosPrestadores,
} from './prestadores-mapa.viewmodel';

const BOGOTA: Posicion = { lat: 4.6432, lng: -74.0631 };

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
  beforeEach(() => jasmine.clock().install());
  afterEach(() => jasmine.clock().uninstall());
  const tick = (ms: number) => jasmine.clock().tick(ms);
  const asentar = async () => {
    for (let vuelta = 0; vuelta < 10; vuelta++) {
      await Promise.resolve();
    }
  };

  interface Opciones {
    claimId?: string | null;
    locale?: Locale;
    cercanos?: (consulta: ConsultaPrestadores) => Observable<BusquedaPrestadores>;
    ciudades?: (pais: Pais) => Observable<CiudadMapa[]>;
    porSiniestro?: (id: string, area?: AreaVisible) => Observable<BusquedaSiniestro | null>;
    mapa?: boolean;
  }

  function crear(geo: GeolocationPort, opciones: Opciones = {}) {
    const consultas: ConsultaPrestadores[] = [];
    const paises: Pais[] = [];
    const siniestros: (AreaVisible | undefined)[] = [];
    const locale = signal<Locale>(opciones.locale ?? 'es-CO');
    const puertos: PuertosPrestadores = {
      cercanos: (consulta) => {
        consultas.push(consulta);
        return opciones.cercanos ? opciones.cercanos(consulta) : of(BUSQUEDA);
      },
      ciudades: (pais) => {
        paises.push(pais);
        return opciones.ciudades ? opciones.ciudades(pais) : of(CIUDADES_CO);
      },
      porSiniestro: (id, area) => {
        siniestros.push(area);
        return opciones.porSiniestro ? opciones.porSiniestro(id, area) : of(BUSQUEDA_SINIESTRO);
      },
    };
    const vm = new PrestadoresMapaViewModel(puertos, geo, opciones.claimId ?? null, locale);
    if (opciones.mapa) {
      vm.fijarMapa('disponible');
    }
    return { vm, consultas, paises, siniestros, locale };
  }

  function concedida(pos: Posicion = BOGOTA): GeolocationPort {
    return { actual: () => Promise.resolve(pos) };
  }

  function negada(code = 1): GeolocationPort {
    return { actual: () => Promise.reject({ code }) };
  }

  describe('navigation and area loading', () => {
    it('starts on the person at zoom 14 with Mi ubicación and waits for the map to stop', async () => {
      const { vm, consultas } = crear(concedida(), { mapa: true });
      vm.cargar();
      await asentar();

      expect(vm.modo()).toBe('nearMe');
      expect(vm.objetivoCamara()).toEqual({ ...BOGOTA, zoom: 14 });
      expect(vm.ciudadMarcada()).toBeNull();
      expect(vm.miUbicacionVisible()).toBeTrue();
      expect(vm.diceCercaDeTi()).toBeTrue();
      expect(vm.referenciaDistancia()).toBe('posicion');
      expect(consultas).toEqual([]);
      expect(vm.status()).toBe('loading');
    });

    it('sends one query 300 ms after the last camera stop with the area, ramo and origin', async () => {
      const { vm, consultas } = crear(concedida(), { mapa: true });
      vm.cargar();
      await asentar();
      vm.seleccionarRamo('soat-motocicleta');
      consultas.length = 0;

      vm.alMoverCamara(AREA_MEDELLIN);
      tick(100);
      vm.alMoverCamara(AREA_MEDELLIN);
      tick(100);
      vm.alMoverCamara(AREA_CHAPINERO);
      tick(299);
      expect(consultas).toEqual([]);
      tick(1);

      expect(consultas).toEqual([
        { ramo: 'soat-motocicleta', pais: 'CO', area: AREA_CHAPINERO, origen: BOGOTA },
      ]);
      expect(vm.area()).toEqual(AREA_CHAPINERO);
      expect(vm.prestadores()[0].id).toBe('PRE-BOG-06');
      expect(vm.status()).toBe('ready');
    });

    it('keeps the markers until the answer arrives and ignores a late answer for an older area', async () => {
      const respuestas: Subject<BusquedaPrestadores>[] = [];
      const { vm } = crear(concedida(), {
        mapa: true,
        cercanos: () => {
          const respuesta = new Subject<BusquedaPrestadores>();
          respuestas.push(respuesta);
          return respuesta;
        },
      });
      vm.cargar();
      await asentar();
      vm.alMoverCamara(AREA_CHAPINERO);
      tick(300);
      respuestas[0].next(BUSQUEDA);

      vm.alMoverCamara(AREA_MEDELLIN);
      tick(300);
      vm.alMoverCamara(AREA_CHAPINERO);
      tick(300);
      expect(vm.status()).toBe('loading');
      expect(vm.prestadores()).toEqual([PRESTADOR]);

      respuestas[1].next({ ...BUSQUEDA, prestadores: [IPS] });
      respuestas[1].error(new Error('tarde'));
      expect(vm.prestadores()).toEqual([PRESTADOR]);

      respuestas[2].next({ ...BUSQUEDA, truncado: true, prestadores: [] });
      expect(vm.status()).toBe('empty');
      expect(vm.truncado()).toBeTrue();
    });

    it('keeps the markers and offers a retry of the same area when an area load fails', async () => {
      let fallar = false;
      const { vm, consultas } = crear(concedida(), {
        mapa: true,
        cercanos: () => (fallar ? throwError(() => new Error('caido')) : of(BUSQUEDA)),
      });
      vm.cargar();
      await asentar();
      vm.alMoverCamara(AREA_CHAPINERO);
      tick(300);
      fallar = true;
      vm.alMoverCamara(AREA_MEDELLIN);
      tick(300);
      expect(vm.status()).toBe('error');
      expect(vm.prestadores()).toEqual([PRESTADOR]);

      fallar = false;
      vm.reintentar();
      expect(consultas.at(-1)?.area).toEqual(AREA_MEDELLIN);
      expect(vm.status()).toBe('ready');
    });

    it('returns to the person at zoom 14 with Mi ubicación and unmarks the city', async () => {
      const { vm } = crear(concedida(), { mapa: true });
      vm.cargar();
      await asentar();
      vm.elegirCiudad(CIUDADES_CO[1]);
      expect(vm.ciudadMarcada()).toBe('Medellín');

      vm.usarMiUbicacion();
      expect(vm.objetivoCamara()).toEqual({ ...BOGOTA, zoom: 14 });
      expect(vm.ciudadMarcada()).toBeNull();
    });

    it('hides Mi ubicación without location and ignores it', async () => {
      const { vm } = crear(negada(), { mapa: true });
      vm.cargar();
      await asentar();
      expect(vm.miUbicacionVisible()).toBeFalse();
      const objetivo = vm.objetivoCamara();
      vm.usarMiUbicacion();
      expect(vm.objetivoCamara()).toBe(objetivo);
    });

    it('queries right away with the 005 modes while there is no map', async () => {
      const { vm, consultas } = crear(concedida());
      vm.cargar();
      await asentar();
      expect(consultas[0]).toEqual({ ramo: null, pais: 'CO', origen: BOGOTA, radioKm: 10 });
      expect(vm.status()).toBe('ready');

      vm.elegirCiudad(CIUDADES_CO[2]);
      expect(consultas.at(-1)).toEqual({ ramo: null, pais: 'CO', ciudad: 'Chía' });
      expect(vm.modo()).toBe('nearMe');

      vm.usarMiUbicacion();
      expect(consultas.at(-1)).toEqual({ ramo: null, pais: 'CO', origen: BOGOTA, radioKm: 10 });
    });

    it('reloads with the fallback when the map fails after a camera target', async () => {
      const { vm, consultas } = crear(concedida(), { mapa: true });
      vm.fijarMapa('no-disponible');
      expect(consultas).toEqual([]);
      vm.fijarMapa('disponible');
      vm.cargar();
      await asentar();
      vm.fijarMapa('disponible');
      expect(consultas).toEqual([]);
      vm.fijarMapa('no-disponible');
      expect(vm.mapa()).toBe('no-disponible');
      expect(consultas).toEqual([{ ramo: null, pais: 'CO', origen: BOGOTA, radioKm: 10 }]);
    });
  });

  describe('city chips by country', () => {
    it('reads the country from the locale and starts on its first city when location is denied', async () => {
      for (const code of [1, 3]) {
        const { vm, consultas, paises } = crear(negada(code), {
          locale: 'es-MX',
          ciudades: () => of(CIUDADES_MX),
        });
        vm.cargar();
        await asentar();

        expect(vm.pais()).toBe('MX');
        expect(paises).toEqual(['MX']);
        expect(vm.ciudades()).toEqual(CIUDADES_MX);
        expect(vm.muestraChips()).toBeTrue();
        expect(vm.modo()).toBe('chooseCity');
        expect(vm.ciudadMarcada()).toBe('Ciudad de México');
        expect(vm.objetivoCamara()).toEqual({ lat: 19.4326, lng: -99.1332, zoom: 11 });
        expect(vm.diceCercaDeTi()).toBeFalse();
        expect(vm.muestraDistancias()).toBeFalse();
        expect(vm.referenciaDistancia()).toBeNull();
        expect(vm.km(PRESTADOR)).toBeNull();
        expect(consultas[0]).toEqual({ ramo: null, pais: 'MX', ciudad: 'Ciudad de México' });
        expect(vm.status()).toBe('ready');
      }
    });

    it('follows the locale for es-CL and es-PE', () => {
      const chile = crear(negada(), { locale: 'es-CL' });
      expect(chile.vm.pais()).toBe('CL');
      chile.locale.set('es-PE');
      expect(chile.vm.pais()).toBe('PE');
    });

    it('targets a chosen city with its zoom, marks it, and a drag unmarks it', async () => {
      const { vm, consultas } = crear(negada(), { mapa: true });
      vm.cargar();
      await asentar();
      expect(consultas).toEqual([]);

      vm.seleccionarRamo('viaje');
      vm.elegirCiudad(CIUDADES_CO[1]);
      expect(vm.objetivoCamara()).toEqual({ lat: 6.2442, lng: -75.5812, zoom: 13 });
      expect(vm.ciudadMarcada()).toBe('Medellín');
      expect(vm.ramo()).toBe('viaje');

      vm.alArrastrar();
      expect(vm.ciudadMarcada()).toBeNull();
      vm.alMoverCamara(AREA_MEDELLIN);
      tick(300);
      expect(consultas.at(-1)).toEqual({ ramo: 'viaje', pais: 'CO', area: AREA_MEDELLIN });
    });

    it('keeps distances from the person after jumping to a city', async () => {
      const { vm, consultas } = crear(concedida(), { mapa: true });
      vm.cargar();
      await asentar();
      vm.elegirCiudad(CIUDADES_CO[1]);
      vm.alMoverCamara(AREA_MEDELLIN);
      tick(300);
      expect(vm.modo()).toBe('nearMe');
      expect(vm.muestraDistancias()).toBeTrue();
      expect(consultas.at(-1)).toEqual({ ramo: null, pais: 'CO', area: AREA_MEDELLIN, origen: BOGOTA });
    });

    it('shows the empty country without chips or camera target', async () => {
      const { vm, consultas } = crear(negada(), { locale: 'es-PE', ciudades: () => of([]) });
      expect(vm.paisVacio()).toBeFalse();
      vm.cargar();
      await asentar();
      expect(vm.paisVacio()).toBeTrue();
      expect(vm.muestraChips()).toBeFalse();
      expect(vm.objetivoCamara()).toBeNull();
      expect(vm.status()).toBe('empty');
      expect(consultas).toEqual([]);
    });

    it('shows a retry when the cities cannot be read, and ignores a stale cities answer', async () => {
      const caido = crear(concedida(), { ciudades: () => throwError(() => new Error('caido')) });
      caido.vm.cargar();
      expect(caido.vm.status()).toBe('error');

      const respuestas: Subject<CiudadMapa[]>[] = [];
      const lento = crear(concedida(), {
        ciudades: () => {
          const respuesta = new Subject<CiudadMapa[]>();
          respuestas.push(respuesta);
          return respuesta;
        },
      });
      lento.vm.cargar();
      lento.vm.cargar();
      respuestas[0].next(CIUDADES_MX);
      respuestas[0].error(new Error('tarde'));
      expect(lento.vm.ciudades()).toEqual([]);
      respuestas[1].next(CIUDADES_CO);
      await asentar();
      expect(lento.vm.ciudades()).toEqual(CIUDADES_CO);
      expect(lento.vm.status()).toBe('ready');
    });

    it('retries location from Usar mi ubicación after a denial', async () => {
      let intentos = 0;
      const { vm, consultas } = crear({
        actual: () => {
          intentos += 1;
          return intentos === 1 ? Promise.reject({ code: 1 }) : Promise.resolve({ lat: 6.2, lng: -75.5 });
        },
      });
      vm.cargar();
      await asentar();
      expect(vm.modo()).toBe('chooseCity');

      vm.usarUbicacion();
      await asentar();
      expect(vm.modo()).toBe('nearMe');
      expect(vm.ciudadMarcada()).toBeNull();
      expect(consultas.at(-1)).toEqual({ ramo: null, pais: 'CO', origen: { lat: 6.2, lng: -75.5 }, radioKm: 10 });
    });

    it('shows a retry when the position fails without being a denial', async () => {
      const raro = crear({ actual: () => Promise.reject(new Error('sensor')) });
      raro.vm.cargar();
      await asentar();
      expect(raro.vm.status()).toBe('error');

      raro.vm.reintentar();
      expect(raro.vm.status()).toBe('loading');
      await asentar();
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
      await asentar();
      expect(exito.consultas).toEqual([
        { ramo: null, pais: 'CO', origen: { lat: 4.6, lng: -74.1 }, radioKm: 10 },
      ]);

      const denegada = diferida();
      denegada.vm.cargar();
      denegada.vm.usarUbicacion();
      denegada.rejecters[0]({ code: 1 });
      denegada.resolvers[1]({ lat: 4.6, lng: -74.1 });
      await asentar();
      expect(denegada.vm.modo()).toBe('nearMe');
    });

    it('shows a read failure without a map', async () => {
      const caido = crear(concedida(), { cercanos: () => throwError(() => new Error('caido')) });
      caido.vm.cargar();
      await asentar();
      expect(caido.vm.status()).toBe('error');
      expect(caido.vm.prestadores()).toEqual([]);
    });
  });

  describe('floating card', () => {
    async function listo() {
      const respuesta = { actual: of<BusquedaPrestadores>({ ...BUSQUEDA, prestadores: [PRESTADOR, IPS] }) };
      const creado = crear(concedida(), { mapa: true, cercanos: () => respuesta.actual });
      creado.vm.cargar();
      await asentar();
      creado.vm.alMoverCamara(AREA_CHAPINERO);
      tick(300);
      return { ...creado, respuesta };
    }

    it('selects a marker, swaps to another and closes', async () => {
      const { vm } = await listo();
      vm.seleccionar([PRESTADOR.id]);
      expect(vm.seleccion()).toEqual([PRESTADOR]);
      vm.seleccionar([IPS.id]);
      expect(vm.seleccion()).toEqual([IPS]);
      vm.cerrarTarjeta();
      expect(vm.seleccion()).toEqual([]);
    });

    it('selects every provider of a stack', async () => {
      const { vm } = await listo();
      vm.seleccionar([PRESTADOR.id, IPS.id]);
      expect(vm.seleccion().map((p) => p.id)).toEqual([PRESTADOR.id, IPS.id]);
    });

    it('keeps the card on camera moves and refreshes its data', async () => {
      const { vm, respuesta } = await listo();
      vm.seleccionar([PRESTADOR.id]);
      respuesta.actual = of({ ...BUSQUEDA, prestadores: [{ ...PRESTADOR, distanciaKm: 2.5 }] });
      vm.alMoverCamara(AREA_CHAPINERO);
      tick(300);
      expect(vm.seleccion()[0].distanciaKm).toBe(2.5);

      respuesta.actual = of({ ...BUSQUEDA, prestadores: [] });
      vm.alMoverCamara(AREA_MEDELLIN);
      tick(300);
      expect(vm.seleccion().map((p) => p.id)).toEqual([PRESTADOR.id]);
    });

    it('closes the card when a ramo answer leaves the provider out', async () => {
      const { vm, respuesta } = await listo();
      vm.seleccionar([IPS.id]);
      respuesta.actual = of({ ...BUSQUEDA, prestadores: [PRESTADOR] });
      vm.seleccionarRamo('soat-motocicleta');
      expect(vm.seleccion()).toEqual([]);
    });

    it('keeps an off-screen provider only while it serves the chosen ramo', async () => {
      const { vm, respuesta } = await listo();
      vm.seleccionar([IPS.id]);
      respuesta.actual = of({ ...BUSQUEDA, prestadores: [] });
      vm.alMoverCamara(AREA_MEDELLIN);
      tick(300);
      vm.seleccionarRamo('viaje');
      expect(vm.seleccion()).toEqual([IPS]);
      vm.seleccionarRamo('pagos');
      expect(vm.seleccion()).toEqual([]);
    });

    it('closes the card without a map area when the provider is missing', async () => {
      const { vm } = crear(concedida(), {
        cercanos: (consulta) => of(consulta.ramo ? { ...BUSQUEDA, prestadores: [] } : BUSQUEDA),
      });
      vm.cargar();
      await asentar();
      vm.seleccionar([PRESTADOR.id]);
      expect(vm.seleccion()).toEqual([PRESTADOR]);
      vm.seleccionarRamo('viaje');
      expect(vm.seleccion()).toEqual([]);
    });

    it('centers a list row at zoom 14 and opens its card', async () => {
      const { vm } = await listo();
      vm.seleccionarDesdeLista(IPS);
      expect(vm.seleccion()).toEqual([IPS]);
      expect(vm.objetivoCamara()).toEqual({ lat: IPS.lat, lng: IPS.lng, zoom: 14 });
    });

    it('expands a row instead when there is no map', async () => {
      const { vm } = crear(concedida());
      vm.cargar();
      await asentar();
      vm.seleccionarDesdeLista(PRESTADOR);
      expect(vm.abiertoId()).toBe(PRESTADOR.id);
      expect(vm.seleccion()).toEqual([]);
      vm.seleccionarDesdeLista(PRESTADOR);
      expect(vm.abiertoId()).toBeNull();
    });

    it('builds the directions, phone and distance labels', () => {
      const { vm } = crear(concedida());
      expect(vm.comoLlegar(PRESTADOR)).toBe(
        'https://www.google.com/maps/dir/?api=1&destination=4.6355,-74.0655',
      );
      expect(vm.llamar(PRESTADOR)).toBe('tel:6015550112');
      expect(vm.km(PRESTADOR)).toBe('0,9');
      expect(vm.km({ ...PRESTADOR, distanciaKm: null })).toBeNull();
    });
  });

  describe('claim mode', () => {
    it('starts at the geotag with zoom 14, no chips, the ramo fixed and the event label', () => {
      const { vm, consultas, paises, siniestros } = crear(concedida(), { claimId: 'sin-1988' });
      vm.cargar();
      expect(vm.modo()).toBe('claim');
      expect(vm.ramoBloqueado()).toBeTrue();
      expect(vm.siniestro()?.numero).toBe('SIN-1988');
      expect(vm.ramo()).toBe('soat-motocicleta');
      expect(vm.centro()).toEqual({ lat: 4.626, lng: -74.15 });
      expect(vm.objetivoCamara()).toEqual({ lat: 4.626, lng: -74.15, zoom: 14 });
      expect(vm.referenciaDistancia()).toBe('evento');
      expect(vm.km(vm.prestadores()[0])).toBe('0,8');
      expect(vm.diceCercaDeTi()).toBeFalse();
      expect(vm.muestraChips()).toBeFalse();
      expect(vm.paisVacio()).toBeFalse();
      expect(vm.miUbicacionVisible()).toBeFalse();
      expect(paises).toEqual([]);
      expect(siniestros).toEqual([undefined]);
      vm.seleccionarRamo('pagos');
      vm.seleccionarRamo(null);
      expect(vm.ramo()).toBe('soat-motocicleta');
      expect(consultas).toEqual([]);
    });

    it('loads the visible area through the claim route without moving the camera', async () => {
      const { vm, consultas, siniestros } = crear(concedida(), { claimId: 'sin-1988', mapa: true });
      vm.cargar();
      vm.alMoverCamara(AREA_CHAPINERO);
      tick(300);
      expect(siniestros).toEqual([undefined, AREA_CHAPINERO]);
      expect(consultas).toEqual([]);
      expect(vm.objetivoCamara()).toEqual({ lat: 4.626, lng: -74.15, zoom: 14 });
      expect(vm.status()).toBe('ready');
    });

    it('falls back to the 10 km claim read when the map is lost before an area', () => {
      const { vm, siniestros } = crear(concedida(), { claimId: 'sin-1988', mapa: true });
      vm.cargar();
      vm.fijarMapa('no-disponible');
      expect(siniestros).toEqual([undefined, undefined]);
      expect(vm.status()).toBe('ready');
    });

    it('handles a missing claim, a failure and a stale answer on area loads', async () => {
      const respuestas: Subject<BusquedaSiniestro | null>[] = [];
      const { vm } = crear(concedida(), {
        claimId: 'sin-1988',
        mapa: true,
        porSiniestro: (_id, area) => {
          if (!area) {
            return of(BUSQUEDA_SINIESTRO);
          }
          const respuesta = new Subject<BusquedaSiniestro | null>();
          respuestas.push(respuesta);
          return respuesta;
        },
      });
      vm.cargar();
      vm.alMoverCamara(AREA_CHAPINERO);
      tick(300);
      vm.alMoverCamara(AREA_MEDELLIN);
      tick(300);
      respuestas[0].next(null);
      respuestas[0].error(new Error('tarde'));
      expect(vm.status()).toBe('loading');

      respuestas[1].error(new Error('caido'));
      expect(vm.status()).toBe('error');
      expect(vm.prestadores().length).toBe(1);

      vm.reintentar();
      respuestas[2].next(null);
      expect(vm.status()).toBe('not-found');
    });

    it('offers near me when the claim has no geotag, and treats a missing center the same way', async () => {
      const sinGeo = crear(concedida(), {
        claimId: 'sin-1',
        porSiniestro: () => of({ ...BUSQUEDA_SINIESTRO, sinGeoetiqueta: true, prestadores: [] }),
      });
      sinGeo.vm.cargar();
      expect(sinGeo.vm.status()).toBe('sin-geo');
      expect(sinGeo.vm.objetivoCamara()).toBeNull();
      sinGeo.vm.usarUbicacion();
      await asentar();
      expect(sinGeo.vm.modo()).toBe('nearMe');
      expect(sinGeo.vm.diceCercaDeTi()).toBeTrue();
      expect(sinGeo.consultas[0].origen).toEqual(BOGOTA);

      const sinCentro = crear(concedida(), {
        claimId: 'sin-2',
        porSiniestro: () => of({ ...BUSQUEDA_SINIESTRO, centro: null }),
      });
      sinCentro.vm.cargar();
      expect(sinCentro.vm.status()).toBe('sin-geo');
    });

    it('shows not-found, an empty claim list, and a retry when the claim read fails', () => {
      const ajeno = crear(concedida(), { claimId: 'ajeno', porSiniestro: () => of(null) });
      ajeno.vm.cargar();
      expect(ajeno.vm.status()).toBe('not-found');
      expect(ajeno.vm.prestadores()).toEqual([]);

      const vacio = crear(concedida(), {
        claimId: 'vacio',
        porSiniestro: () => of({ ...BUSQUEDA_SINIESTRO, prestadores: [] }),
      });
      vacio.vm.cargar();
      expect(vacio.vm.status()).toBe('empty');

      const caido = crear(concedida(), {
        claimId: 'caido',
        porSiniestro: () => throwError(() => new Error('caido')),
      });
      caido.vm.cargar();
      expect(caido.vm.status()).toBe('error');
    });

    it('ignores a stale claim response after the customer asks for their location', async () => {
      const stream = new Subject<BusquedaSiniestro | null>();
      const resolvers: ((pos: Posicion) => void)[] = [];
      const { vm } = crear(
        { actual: () => new Promise((resolve) => resolvers.push(resolve)) },
        { claimId: 'sin-1988', porSiniestro: () => stream },
      );
      vm.cargar();
      vm.usarUbicacion();
      stream.next(BUSQUEDA_SINIESTRO);
      stream.error(new Error('tarde'));
      expect(vm.siniestro()).toBeNull();
      expect(vm.status()).toBe('loading');
      resolvers[0]({ lat: 4, lng: -74 });
      await asentar();
      expect(vm.modo()).toBe('nearMe');
      expect(vm.status()).toBe('ready');
    });
  });
});
