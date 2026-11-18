import { Observable, of, Subject, throwError } from 'rxjs';
import { CiudadMapa } from '../../../prestadores/prestadores.gateway';
import { CIUDADES_CO } from '../../../prestadores/prestadores.testing';
import { Pais } from '../../../prestadores/tipo-prestador';
import { ListadoOperador, PrestadorOperador } from '../bo-prestadores.gateway';
import { BoPrestadoresListaViewModel } from './bo-prestadores-lista.viewmodel';

const FILA: PrestadorOperador = {
  id: 'PRE-BOG-06',
  nombre: 'Taller Moto Chapinero',
  tipo: 'taller-motos',
  ramos: ['soat-motocicleta'],
  direccion: 'Cra 13',
  pais: 'CO',
  ciudad: 'Bogotá',
  barrio: 'Chapinero',
  lat: 4.63,
  lng: -74.06,
  telefono: '601',
  horario: 'Lun',
  estado: 'activo',
  actualizadoEn: '2026-11-17T00:00:00Z',
};

const OTRA: PrestadorOperador = { ...FILA, id: 'PRE-MED-01', ciudad: 'Medellín', nombre: 'Otra' };

const CIUDADES_CL: CiudadMapa[] = [
  { nombre: 'Santiago', lat: -33.4489, lng: -70.6693, zoom: 11, prestadores: 7 },
  { nombre: 'Valparaíso', lat: -33.0472, lng: -71.6127, zoom: 13, prestadores: 3 },
  { nombre: 'Concepción', lat: -36.827, lng: -73.0503, zoom: 13, prestadores: 0 },
];

describe('BoPrestadoresListaViewModel', () => {
  function crear(canWrite = true) {
    const filtros: unknown[] = [];
    const estados: string[] = [];
    const paises: Pais[] = [];
    let ciudades: (pais: Pais) => Observable<CiudadMapa[]> = (pais) =>
      of(pais === 'CL' ? CIUDADES_CL : CIUDADES_CO);
    let listado: Observable<ListadoOperador> = of({
      pais: 'CO' as Pais,
      conteos: { Bogotá: 30, Medellín: 20, Chía: 10 },
      centro: { lat: 4.6, lng: -74.08 },
      prestadores: [FILA, OTRA],
    });
    let estado$ = of({ ...FILA, estado: 'inactivo' as const });
    const vm = new BoPrestadoresListaViewModel(
      {
        listar: (filtro) => {
          filtros.push(filtro);
          return listado;
        },
        ciudades: (pais) => {
          paises.push(pais);
          return ciudades(pais);
        },
        cambiarEstado: (id, estado) => {
          estados.push(`${id}:${estado}`);
          return estado$;
        },
      },
      canWrite,
      'CO',
    );
    return {
      vm,
      filtros,
      estados,
      paises,
      usarCiudades: (fuente: (pais: Pais) => Observable<CiudadMapa[]>) => {
        ciudades = fuente;
      },
      usarListado: (nuevo: Observable<ListadoOperador>) => {
        listado = nuevo;
      },
      fallarLista: () => {
        listado = throwError(() => new Error('caido'));
      },
      vaciar: () => {
        listado = of({
          pais: 'CO' as Pais,
          conteos: { Bogotá: 30, Medellín: 20, Chía: 10 },
          centro: { lat: 4.6, lng: -74.08 },
          prestadores: [],
        });
      },
      fallarEstado: () => {
        estado$ = throwError(() => new Error('no'));
      },
    };
  }

  it('loads cities, counts and rows, then filters and clears them', () => {
    const { vm, filtros, paises } = crear();
    vm.iniciar();
    expect(vm.status()).toBe('ready');
    expect(paises).toEqual(['CO']);
    expect(vm.ciudades()).toEqual(CIUDADES_CO);
    expect(vm.conteos()).toEqual({ Bogotá: 30, Medellín: 20, Chía: 10 });
    expect(vm.resumenConteos()).toBe('Bogotá 30 · Medellín 20 · Chía 10');
    expect(vm.prestadores().length).toBe(2);
    expect(filtros[0]).toEqual({ pais: 'CO' });

    vm.filtrarRamo('soat-motocicleta');
    vm.filtrarCiudad('Chía');
    vm.filtrarEstado('activo');
    expect(filtros.at(-1)).toEqual({
      pais: 'CO',
      ramo: 'soat-motocicleta',
      ciudad: 'Chía',
      estado: 'activo',
    });

    vm.quitarFiltros();
    expect(vm.ramo()).toBe('');
    expect(vm.ciudad()).toBe('');
    expect(vm.estado()).toBe('');
    expect(filtros.at(-1)).toEqual({ pais: 'CO' });
  });

  it('switches country: reloads the city catalog, clears the city and reads any city counts', () => {
    const { vm, filtros, paises, usarListado } = crear();
    vm.iniciar();
    vm.filtrarCiudad('Chía');
    usarListado(
      of({
        pais: 'CL' as Pais,
        conteos: { Santiago: 7, Valparaíso: 3 },
        centro: null,
        prestadores: [],
      }),
    );

    vm.filtrarPais('CL');

    expect(vm.pais()).toBe('CL');
    expect(vm.ciudad()).toBe('');
    expect(paises).toEqual(['CO', 'CL']);
    expect(filtros.at(-1)).toEqual({ pais: 'CL' });
    expect(vm.ciudades().map((ciudad) => ciudad.nombre)).toEqual([
      'Santiago',
      'Valparaíso',
      'Concepción',
    ]);
    expect(vm.resumenConteos()).toBe('Santiago 7 · Valparaíso 3 · Concepción 0');
    expect(vm.status()).toBe('empty');
    expect(vm.centroMapa()).toEqual({ lat: -33.4489, lng: -70.6693 });
  });

  it('centers the map on the answer, then the first row, then the first city', () => {
    const { vm, usarListado, usarCiudades } = crear();
    expect(vm.centroMapa()).toBeNull();
    vm.iniciar();
    expect(vm.centroMapa()).toEqual({ lat: 4.6, lng: -74.08 });

    usarListado(of({ pais: 'CO' as Pais, conteos: {}, centro: null, prestadores: [OTRA] }));
    vm.cargar();
    expect(vm.centroMapa()).toEqual({ lat: OTRA.lat, lng: OTRA.lng });

    usarCiudades(() => throwError(() => new Error('caido')));
    vm.filtrarPais('PE');
    expect(vm.ciudades()).toEqual([]);
    expect(vm.resumenConteos()).toBe('');
  });

  it('ignores a city catalog that arrives after another country was picked', () => {
    const { vm, usarCiudades } = crear();
    const lento = new Subject<CiudadMapa[]>();
    usarCiudades((pais) => (pais === 'MX' ? lento : of(CIUDADES_CL)));
    vm.filtrarPais('MX');
    vm.filtrarPais('CL');
    lento.next(CIUDADES_CO);
    expect(vm.ciudades()).toEqual(CIUDADES_CL);
  });

  it('uses the empty state instead of an error when the filter matches nothing', () => {
    const { vm, vaciar } = crear();
    vaciar();
    vm.cargar();
    expect(vm.status()).toBe('empty');
    expect(vm.prestadores()).toEqual([]);
  });

  it('stays on error when the catalog cannot be read', () => {
    const { vm, fallarLista } = crear();
    fallarLista();
    vm.cargar();
    expect(vm.status()).toBe('error');
  });

  it('inactivates after confirmation and reactivates without one', () => {
    const { vm, estados } = crear();
    vm.cargar();
    vm.confirmarInactivar();
    expect(estados).toEqual([]);

    vm.pedirInactivar(FILA);
    expect(vm.confirmando()?.id).toBe(FILA.id);
    vm.cancelarConfirmacion();
    expect(vm.confirmando()).toBeNull();

    vm.pedirInactivar(FILA);
    vm.confirmarInactivar();
    expect(estados).toEqual(['PRE-BOG-06:inactivo']);
    expect(vm.prestadores()[0].estado).toBe('inactivo');
    expect(vm.prestadores()[1].id).toBe('PRE-MED-01');
    expect(vm.confirmando()).toBeNull();

    vm.reactivar(vm.prestadores()[0]);
    expect(estados.at(-1)).toBe('PRE-BOG-06:activo');
  });

  it('keeps the list when the status change fails', () => {
    const { vm, fallarEstado } = crear();
    vm.cargar();
    fallarEstado();
    vm.reactivar(FILA);
    expect(vm.errorAccion()).toBeTrue();
    expect(vm.status()).toBe('ready');
    expect(vm.prestadores()[0].estado).toBe('activo');
  });

  it('refuses writes for the asesor', () => {
    const { vm, estados } = crear(false);
    expect(vm.canWrite).toBeFalse();
    vm.pedirInactivar(FILA);
    vm.reactivar(FILA);
    expect(vm.confirmando()).toBeNull();
    expect(estados).toEqual([]);
  });
});
