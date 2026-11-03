import { HttpErrorResponse } from '@angular/common/http';
import { of, Subject, throwError } from 'rxjs';
import { POLIZAS } from '../../polizas/polizas.testing';
import { AvisoRecibido, NuevoAviso, Ubicacion } from '../siniestros.gateway';
import {
  Dependencias,
  ReportarSiniestroViewModel,
  TAMANO_MAXIMO,
} from './reportar-siniestro.viewmodel';

describe('ReportarSiniestroViewModel', () => {
  const PNG = new File(['png'], 'dano.png', { type: 'image/png' });
  const RECIBIDO: AvisoRecibido = { id: 'id-1', siniestroId: 'SIN-1001', estado: 'recibido' };

  function crear(cambios: Partial<Dependencias> = {}) {
    const envios: { aviso: NuevoAviso; clave: string }[] = [];
    let claves = 0;
    const vm = new ReportarSiniestroViewModel({
      polizas: () => of(POLIZAS),
      enviar: (aviso, clave) => {
        envios.push({ aviso, clave });
        return of(RECIBIDO);
      },
      ubicar: () => Promise.resolve({ lat: 4.65, lng: -74.08, precisionM: 12 }),
      hoy: () => '2026-11-02',
      nuevaClave: () => `clave-${++claves}`,
      ...cambios,
    });
    return { vm, envios };
  }

  function llenar(vm: ReportarSiniestroViewModel) {
    vm.cargarPolizas();
    vm.fechaHecho.set('2026-11-01');
    vm.descripcion.set('Pantalla rota');
    vm.continuar();
  }

  it('solo ofrece pólizas vigentes y preselecciona si hay una', () => {
    const { vm } = crear();
    vm.cargarPolizas();
    expect(vm.polizas().map((p) => p.estado)).toEqual(['VIGENTE']);
    expect(vm.poliza()).toBe(POLIZAS[0].numero);
    expect(vm.ramoSeleccionado()).toBe('Hogar');
  });

  it('sin pólizas vigentes no deja reportar', () => {
    const { vm } = crear({ polizas: () => of([POLIZAS[1]]) });
    vm.cargarPolizas();
    expect(vm.polizasStatus()).toBe('sin-polizas');
  });

  it('no continúa a evidencia con fecha futura ni sin descripción', () => {
    const { vm } = crear();
    vm.cargarPolizas();
    vm.fechaHecho.set('2026-11-03');
    vm.continuar();
    expect(vm.paso()).toBe('formulario');
    expect(vm.errores().fechaHecho).toBeTrue();
    expect(vm.errores().descripcion).toBeTrue();
  });

  it('valida tipo y tamaño del archivo como el núcleo', () => {
    const { vm } = crear();
    vm.elegirArchivo(new File(['x'], 'virus.exe', { type: 'application/x-msdownload' }));
    expect(vm.errorArchivo()).toBe('tipo');
    expect(vm.puedeEnviar()).toBeFalse();

    const grande = new File([new Uint8Array(TAMANO_MAXIMO + 1)], 'grande.png', {
      type: 'image/png',
    });
    vm.elegirArchivo(grande);
    expect(vm.errorArchivo()).toBe('tamano');

    vm.elegirArchivo(PNG);
    expect(vm.errorArchivo()).toBeNull();
    expect(vm.puedeEnviar()).toBeTrue();
  });

  it('guarda la ubicación si el usuario la permite', async () => {
    const { vm } = crear();
    await vm.usarUbicacion();
    expect(vm.ubicacionStatus()).toBe('guardada');
    expect(vm.ubicacion()).toEqual({ lat: 4.65, lng: -74.08, precisionM: 12 });
  });

  it('si el usuario bloquea la ubicación el aviso sigue sin geoetiqueta', async () => {
    const { vm, envios } = crear({
      ubicar: () => Promise.reject(new Error('denegada')) as Promise<Ubicacion>,
    });
    llenar(vm);
    await vm.usarUbicacion();
    expect(vm.ubicacionStatus()).toBe('bloqueada');

    vm.elegirArchivo(PNG);
    vm.enviar();

    expect(envios[0].aviso.ubicacion).toBeNull();
    expect(vm.paso()).toBe('enviado');
    expect(vm.recibido()?.siniestroId).toBe('SIN-1001');
  });

  it('reintentar tras un error de red reutiliza la clave: no duplica el aviso', () => {
    let intentos = 0;
    const claves: string[] = [];
    const { vm } = crear({
      enviar: (_aviso, clave) => {
        claves.push(clave);
        return ++intentos === 1
          ? throwError(() => new HttpErrorResponse({ status: 503 }))
          : of(RECIBIDO);
      },
    });
    llenar(vm);
    vm.elegirArchivo(PNG);

    vm.enviar();
    expect(vm.envio()).toBe('error');
    vm.enviar();

    expect(claves).toEqual(['clave-1', 'clave-1']);
    expect(vm.paso()).toBe('enviado');
  });

  it('un rechazo del núcleo muestra el mensaje y renueva la clave', () => {
    const claves: string[] = [];
    const { vm } = crear({
      enviar: (_a, clave) => {
        claves.push(clave);
        return throwError(
          () =>
            new HttpErrorResponse({
              status: 422,
              error: { codigo: 'x', mensaje: 'La evidencia debe ser PNG' },
            }),
        );
      },
    });
    llenar(vm);
    vm.elegirArchivo(PNG);
    vm.enviar();
    expect(vm.envio()).toBe('rechazado');
    expect(vm.rechazo()).toBe('La evidencia debe ser PNG');
    vm.enviar();
    expect(claves).toEqual(['clave-1', 'clave-2']);
  });

  it('no envía dos veces mientras espera la respuesta', () => {
    const pendiente = new Subject<AvisoRecibido>();
    let llamadas = 0;
    const { vm } = crear({
      enviar: () => {
        llamadas++;
        return pendiente;
      },
    });
    llenar(vm);
    vm.elegirArchivo(PNG);
    vm.enviar();
    vm.enviar();
    expect(llamadas).toBe(1);
    expect(vm.puedeEnviar()).toBeFalse();
  });
});
