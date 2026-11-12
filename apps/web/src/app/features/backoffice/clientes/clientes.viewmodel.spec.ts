import { HttpErrorResponse } from '@angular/common/http';
import { of, Subject, throwError } from 'rxjs';
import { Cliente, ConsultaClientes, PaginaClientes } from './clientes.gateway';
import { CLIENTES } from './clientes.testing';
import { ClientesViewModel, nombreCliente, PuertosClientes, pushDe } from './clientes.viewmodel';

describe('ClientesViewModel', () => {
  function pagina(clientes: Cliente[], hayMas = false, numero = 1): PaginaClientes {
    return { clientes, pagina: numero, hayMas };
  }

  function crear(respuesta: PaginaClientes | Subject<PaginaClientes> = pagina(CLIENTES), puedeEditar = true) {
    const consultas: ConsultaClientes[] = [];
    const escrituras: string[] = [];
    const puertos: PuertosClientes = {
      listar: (consulta) => {
        consultas.push(consulta);
        return respuesta instanceof Subject ? respuesta : of(respuesta);
      },
      crear: (body) => {
        escrituras.push(`crear:${body.email}`);
        return of(CLIENTES[0]);
      },
      editar: (usuarioId, body) => {
        escrituras.push(`editar:${usuarioId}:${body.email}`);
        return of(CLIENTES[0]);
      },
      cambiarEstado: (usuarioId, estado) => {
        escrituras.push(`estado:${usuarioId}:${estado}`);
        return of({ ...CLIENTES[0], estado });
      },
    };
    return { vm: new ClientesViewModel(puertos, puedeEditar), consultas, escrituras, puertos };
  }

  it('stays loading until the BFF answers', () => {
    const pending = new Subject<PaginaClientes>();
    const { vm } = crear(pending);

    vm.cargar();

    expect(vm.status()).toBe('loading');
    expect(vm.clientes()).toEqual([]);
  });

  it('searches, filters by status and pages', () => {
    let actual = pagina(CLIENTES, true, 1);
    const consultas: ConsultaClientes[] = [];
    const vm = new ClientesViewModel(
      {
        listar: (consulta) => {
          consultas.push(consulta);
          return of(actual);
        },
        crear: () => of(CLIENTES[0]),
        editar: () => of(CLIENTES[0]),
        cambiarEstado: () => of(CLIENTES[0]),
      },
      true,
    );

    vm.buscar('Ana');
    expect(consultas.at(-1)).toEqual({ q: 'Ana', estado: '', pagina: 1 });
    expect(vm.status()).toBe('ready');
    expect(vm.hayMas()).toBeTrue();

    vm.filtrar('INACTIVO');
    expect(consultas.at(-1)).toEqual({ q: 'Ana', estado: 'INACTIVO', pagina: 1 });

    actual = pagina([], false, 2);
    vm.siguiente();
    expect(consultas.at(-1)).toEqual({ q: 'Ana', estado: 'INACTIVO', pagina: 2 });
    expect(vm.pagina()).toBe(2);
    expect(vm.hayMas()).toBeFalse();
  });

  it('reads the Push column as yes, no or unknown', () => {
    expect(CLIENTES.map(pushDe)).toEqual(['si', 'no', 'desconocido']);
    expect(nombreCliente(CLIENTES[0])).toBe('Andrés Gómez');
    expect(nombreCliente({ ...CLIENTES[1], nombre: '  ', apellidos: '' })).toBe(CLIENTES[1].email);
  });

  it('creates and edits through the form', () => {
    const { vm, escrituras } = crear();
    vm.cargar();

    vm.abrirCrear();
    vm.editarCampo('nombre', 'Ana');
    vm.editarCampo('apellidos', 'Ruiz');
    vm.editarCampo('email', 'ana@correo.com');
    vm.editarCampo('documento', '1020');
    vm.editarCampo('password', 'secreto');
    expect(vm.puedeGuardar()).toBeTrue();
    vm.guardar();
    expect(escrituras).toEqual(['crear:ana@correo.com']);
    expect(vm.formulario()).toBeNull();

    vm.abrirEditar(CLIENTES[0]);
    vm.editarCampo('email', 'nueva@correo.com');
    vm.guardar();
    expect(escrituras.at(-1)).toBe(`editar:${CLIENTES[0].usuarioId}:nueva@correo.com`);
  });

  it('deactivates only after confirmation and reactivates directly', () => {
    const { vm, escrituras } = crear();
    vm.cargar();

    vm.pedirDesactivar(CLIENTES[0].usuarioId);
    expect(vm.confirmando()).toBe(CLIENTES[0].usuarioId);
    expect(escrituras).toEqual([]);

    vm.confirmarDesactivacion();
    expect(escrituras).toEqual([`estado:${CLIENTES[0].usuarioId}:INACTIVO`]);

    vm.reactivar(CLIENTES[2].usuarioId);
    expect(escrituras.at(-1)).toBe(`estado:${CLIENTES[2].usuarioId}:ACTIVO`);
  });

  it('keeps the conflict message from a duplicate email', () => {
    const { vm, puertos } = crear();
    vm.cargar();
    puertos.crear = () =>
      throwError(
        () => new HttpErrorResponse({ status: 409, error: { mensaje: 'El correo ya existe' } }),
      );
    vm.abrirCrear();
    vm.editarCampo('nombre', 'Ana');
    vm.editarCampo('apellidos', 'Ruiz');
    vm.editarCampo('email', 'ana@correo.com');
    vm.editarCampo('documento', '1020');
    vm.editarCampo('password', 'secreto');
    vm.guardar();

    expect(vm.conflicto()).toBe('El correo ya existe');
    expect(vm.formulario()).toBe('crear');
  });

  it('reports an empty page', () => {
    const { vm } = crear(pagina([]));
    vm.cargar();
    expect(vm.status()).toBe('empty');
  });

  it('pages backward, ignores the next page when there is none, and records lookup failures', () => {
    let actual = pagina(CLIENTES, true, 1);
    const consultas: ConsultaClientes[] = [];
    const puertos: PuertosClientes = {
      listar: (consulta) => {
        consultas.push(consulta);
        return of(actual);
      },
      crear: () => of(CLIENTES[0]),
      editar: () =>
        throwError(() => new HttpErrorResponse({ status: 404, error: { mensaje: 'No existe' } })),
      cambiarEstado: () => throwError(() => new HttpErrorResponse({ status: 503 })),
    };
    const vm = new ClientesViewModel(puertos, true);
    vm.cargar();
    actual = pagina(CLIENTES, false, 2);
    vm.siguiente();
    expect(vm.pagina()).toBe(2);
    const antes = consultas.length;
    vm.siguiente();
    expect(consultas.length).toBe(antes);
    actual = pagina(CLIENTES, true, 1);
    vm.anterior();
    expect(vm.pagina()).toBe(1);

    vm.abrirEditar(CLIENTES[0]);
    vm.guardar();
    expect(vm.noEncontrado()).toBeTrue();

    vm.reactivar(CLIENTES[2].usuarioId);
    expect(vm.status()).toBe('error');
  });

  it('lets the advisor read the list without editing', () => {
    const { vm, escrituras } = crear(pagina(CLIENTES), false);
    vm.cargar();

    expect(vm.puedeEditar).toBeFalse();
    expect(vm.status()).toBe('ready');
    expect(vm.clientes().length).toBe(CLIENTES.length);
    vm.abrirCrear();
    vm.pedirDesactivar(CLIENTES[0].usuarioId);
    vm.reactivar(CLIENTES[2].usuarioId);
    expect(vm.formulario()).toBeNull();
    expect(vm.confirmando()).toBeNull();
    expect(escrituras).toEqual([]);
  });
});
