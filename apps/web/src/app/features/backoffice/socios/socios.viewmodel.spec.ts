import { HttpErrorResponse } from '@angular/common/http';
import { Observable, of, Subject, throwError } from 'rxjs';
import { ListaSocios, SocioCreado } from './socios.gateway';
import { ACTIVO_ID, CREADO, REVOCADO_ID, SOCIOS, VIGENTE_ID } from './socios.testing';
import { PuertosSocios, SociosViewModel } from './socios.viewmodel';

describe('SociosViewModel', () => {
  function crear(
    opciones: {
      lista?: ListaSocios | Subject<ListaSocios> | Observable<never>;
      alta?: Observable<SocioCreado>;
      sobre?: Partial<PuertosSocios>;
    } = {},
  ) {
    const llamadas: string[] = [];
    const lista = opciones.lista ?? { socios: SOCIOS };
    const puertos: PuertosSocios = {
      listar: () => {
        llamadas.push('listar');
        return lista instanceof Observable ? lista : of(lista);
      },
      crear: (body) => {
        llamadas.push(`crear:${body.nombre}:${body.alcances.join(',')}`);
        return opciones.alta ?? of(CREADO);
      },
      rotar: (socioId) => {
        llamadas.push(`rotar:${socioId}`);
        return of({ credencialId: 'nueva', apiKey: 'sk_rotada_456' });
      },
      revocarCredencial: (socioId, credencialId) => {
        llamadas.push(`credencial:${socioId}:${credencialId}`);
        return of(undefined);
      },
      revocar: (socioId) => {
        llamadas.push(`revocar:${socioId}`);
        return of({ ...SOCIOS[0], estado: 'revocado' as const });
      },
    };
    return { vm: new SociosViewModel({ ...puertos, ...opciones.sobre }), llamadas };
  }

  function conflicto(mensaje: string, status = 409) {
    return throwError(
      () => new HttpErrorResponse({ status, error: { codigo: 'SOCIO_DUPLICADO', mensaje } }),
    );
  }

  it('stays loading until the BFF answers', () => {
    const { vm } = crear({ lista: new Subject<ListaSocios>() });

    vm.cargar();

    expect(vm.status()).toBe('loading');
  });

  it('is ready with the listed partners', () => {
    const { vm } = crear();

    vm.cargar();

    expect(vm.status()).toBe('ready');
    expect(vm.socios()).toEqual(SOCIOS);
  });

  it('is empty when there are no partners', () => {
    const { vm } = crear({ lista: { socios: [] } });

    vm.cargar();

    expect(vm.status()).toBe('empty');
  });

  it('is in error when the list fails', () => {
    const { vm } = crear({ lista: throwError(() => new Error('caido')) });

    vm.cargar();

    expect(vm.status()).toBe('error');
  });

  it('does not create a partner without a name', () => {
    const { vm, llamadas } = crear();
    vm.abrirCrear();
    vm.editarNombre('   ');
    vm.alternarAlcance('catalogo:leer');

    vm.guardar();

    expect(vm.puedeGuardar()).toBeFalse();
    expect(llamadas).toEqual([]);
  });

  it('does not create a partner with a name longer than 120 characters', () => {
    const { vm, llamadas } = crear();
    vm.abrirCrear();
    vm.editarNombre('a'.repeat(121));
    vm.alternarAlcance('catalogo:leer');

    vm.guardar();

    expect(llamadas).toEqual([]);
  });

  it('does not create a partner without a scope', () => {
    const { vm, llamadas } = crear();
    vm.abrirCrear();
    vm.editarNombre('Aliado');
    vm.alternarAlcance('catalogo:leer');
    vm.alternarAlcance('catalogo:leer');

    vm.guardar();

    expect(vm.puedeGuardar()).toBeFalse();
    expect(llamadas).toEqual([]);
  });

  it('shows the created key once, refreshes the list and clears the key on dismiss', () => {
    const { vm, llamadas } = crear();
    vm.abrirCrear();
    vm.editarNombre('  Nuevo aliado ');
    vm.alternarAlcance('catalogo:leer');
    vm.alternarAlcance('cotizaciones:leer');

    vm.guardar();

    expect(llamadas).toEqual(['crear:Nuevo aliado:catalogo:leer,cotizaciones:leer', 'listar']);
    expect(vm.formularioAbierto()).toBeFalse();
    expect(vm.claveNueva()).toEqual({ nombre: 'Nuevo aliado', apiKey: CREADO.apiKey });

    vm.cerrarClave();

    expect(vm.claveNueva()).toBeNull();
  });

  it('shows the backend message when the partner already exists', () => {
    const { vm } = crear({ alta: conflicto('Ya existe un socio con ese nombre') });
    vm.abrirCrear();
    vm.editarNombre('Aliado local');
    vm.alternarAlcance('catalogo:leer');

    vm.guardar();

    expect(vm.mensaje()).toBe('Ya existe un socio con ese nombre');
    expect(vm.formularioAbierto()).toBeTrue();
    expect(vm.claveNueva()).toBeNull();
  });

  it('shows the backend message when the data is rejected', () => {
    const { vm } = crear({ alta: conflicto('Alcance no válido', 422) });
    vm.abrirCrear();
    vm.editarNombre('Aliado');
    vm.alternarAlcance('catalogo:leer');

    vm.guardar();

    expect(vm.mensaje()).toBe('Alcance no válido');
  });

  it('shows the new key once after rotating and refreshes the list', () => {
    const { vm, llamadas } = crear();
    vm.cargar();

    vm.rotar(SOCIOS[0]);

    expect(llamadas).toEqual(['listar', `rotar:${ACTIVO_ID}`, 'listar']);
    expect(vm.claveNueva()).toEqual({ nombre: 'Aliado local', apiKey: 'sk_rotada_456' });
  });

  it('revokes a credential only after confirming and refreshes the list', () => {
    const { vm, llamadas } = crear();
    vm.cargar();

    vm.pedirRevocarCredencial(ACTIVO_ID, VIGENTE_ID);
    expect(llamadas).toEqual(['listar']);
    vm.confirmar();

    expect(llamadas).toEqual(['listar', `credencial:${ACTIVO_ID}:${VIGENTE_ID}`, 'listar']);
    expect(vm.confirmando()).toBeNull();
  });

  it('revokes a partner only after confirming and refreshes the list', () => {
    const { vm, llamadas } = crear();
    vm.cargar();

    vm.pedirRevocarSocio(ACTIVO_ID);
    vm.cancelarConfirmacion();
    vm.confirmar();
    expect(llamadas).toEqual(['listar']);

    vm.pedirRevocarSocio(ACTIVO_ID);
    vm.confirmar();

    expect(llamadas).toEqual(['listar', `revocar:${ACTIVO_ID}`, 'listar']);
  });

  it('offers no actions for a revoked partner', () => {
    const { vm, llamadas } = crear();
    vm.cargar();

    expect(vm.admiteAcciones(SOCIOS[0])).toBeTrue();
    expect(vm.admiteAcciones(SOCIOS[1])).toBeFalse();
    vm.rotar(SOCIOS[1]);
    vm.pedirRevocarSocio(REVOCADO_ID);
    vm.confirmar();
    vm.pedirRevocarCredencial(REVOCADO_ID, SOCIOS[1].credenciales[0].credencialId);
    vm.confirmar();

    expect(llamadas).toEqual(['listar']);
    expect(vm.claveNueva()).toBeNull();
  });

  it('closes the create form and clears the backend message', () => {
    const { vm } = crear({ alta: conflicto('Ya existe') });
    vm.abrirCrear();
    vm.editarNombre('Aliado');
    vm.alternarAlcance('catalogo:leer');
    vm.guardar();

    vm.cerrarFormulario();

    expect(vm.formularioAbierto()).toBeFalse();
    expect(vm.mensaje()).toBeNull();
  });

  it('shows the backend message when rotating fails', () => {
    const { vm } = crear({ sobre: { rotar: () => conflicto('El socio está revocado') } });
    vm.cargar();

    vm.rotar(SOCIOS[0]);

    expect(vm.mensaje()).toBe('El socio está revocado');
    expect(vm.claveNueva()).toBeNull();
  });

  it('shows the backend message when revoking fails', () => {
    const { vm } = crear({
      sobre: { revocarCredencial: () => conflicto('La clave ya estaba revocada', 404) },
    });
    vm.cargar();

    vm.pedirRevocarCredencial(ACTIVO_ID, VIGENTE_ID);
    vm.confirmar();

    expect(vm.mensaje()).toBe('La clave ya estaba revocada');
    expect(vm.status()).toBe('ready');
  });

  it('is in error when a write fails without a backend message', () => {
    const { vm } = crear({ sobre: { revocar: () => throwError(() => new Error('caido')) } });
    vm.cargar();

    vm.pedirRevocarSocio(ACTIVO_ID);
    vm.confirmar();

    expect(vm.status()).toBe('error');
    expect(vm.mensaje()).toBeNull();
  });
});
