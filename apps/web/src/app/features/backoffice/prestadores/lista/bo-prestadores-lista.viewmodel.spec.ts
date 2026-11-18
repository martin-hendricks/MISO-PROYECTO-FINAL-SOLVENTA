import { of, throwError } from 'rxjs';
import { PrestadorOperador } from '../bo-prestadores.gateway';
import { BoPrestadoresListaViewModel } from './bo-prestadores-lista.viewmodel';

const FILA: PrestadorOperador = {
  id: 'PRE-BOG-06',
  nombre: 'Taller Moto Chapinero',
  tipo: 'taller-motos',
  ramos: ['soat-motocicleta'],
  direccion: 'Cra 13',
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

describe('BoPrestadoresListaViewModel', () => {
  function crear(canWrite = true) {
    const filtros: unknown[] = [];
    const estados: string[] = [];
    let listado = of({
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
        cambiarEstado: (id, estado) => {
          estados.push(`${id}:${estado}`);
          return estado$;
        },
      },
      canWrite,
    );
    return {
      vm,
      filtros,
      estados,
      fallarLista: () => {
        listado = throwError(() => new Error('caido'));
      },
      vaciar: () => {
        listado = of({
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

  it('loads counts and rows, then filters and clears them', () => {
    const { vm, filtros } = crear();
    vm.cargar();
    expect(vm.status()).toBe('ready');
    expect(vm.conteos()).toEqual({ Bogotá: 30, Medellín: 20, Chía: 10 });
    expect(vm.bogota()).toBe(30);
    expect(vm.medellin()).toBe(20);
    expect(vm.chia()).toBe(10);
    expect(vm.prestadores().length).toBe(2);
    expect(filtros[0]).toEqual({});

    vm.filtrarRamo('soat-motocicleta');
    vm.filtrarCiudad('Chía');
    vm.filtrarEstado('activo');
    expect(filtros.at(-1)).toEqual({
      ramo: 'soat-motocicleta',
      ciudad: 'Chía',
      estado: 'activo',
    });

    vm.quitarFiltros();
    expect(vm.ramo()).toBe('');
    expect(vm.ciudad()).toBe('');
    expect(vm.estado()).toBe('');
    expect(filtros.at(-1)).toEqual({});
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
