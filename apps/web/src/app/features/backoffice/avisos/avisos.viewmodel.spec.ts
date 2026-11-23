import { HttpErrorResponse } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { CasoAviso, Cola, ResultadoPago } from './avisos.gateway';
import { CASO, CASO_BAJO_MONTO, COLA, COLA_VACIA } from './avisos.testing';
import { AvisosViewModel, Puertos } from './avisos.viewmodel';

describe('AvisosViewModel', () => {
  function crear(cambios: Partial<Puertos> = {}, caso: CasoAviso = CASO) {
    const llamadas: string[] = [];
    const vm = new AvisosViewModel({
      cola: (filtro) => {
        llamadas.push(`cola:${filtro}`);
        return of<Cola>({ ...COLA, filtro });
      },
      caso: () => of(caso),
      decidir: (_id, decision, motivo) => {
        llamadas.push(`decidir:${decision}:${motivo}`);
        const resultado = decision === 'aprobar' ? 'aprobado' : 'rechazado';
        return of({
          ...caso,
          estado: 'decidido',
          resultado,
          estadoCola: resultado,
          requiereRevision: false,
        });
      },
      enrutar: (_id, motivo) => {
        llamadas.push(`perito:${motivo}`);
        return of({ ...caso, estado: 'enrutado', estadoCola: 'enrutado' as const });
      },
      pagar: () => of({} as ResultadoPago),
      ...cambios,
    });
    return { vm, llamadas };
  }

  function enfocarBoton(): HTMLButtonElement {
    const boton = document.createElement('button');
    document.body.appendChild(boton);
    boton.focus();
    return boton;
  }

  it('abre el primer caso de la cola sin cambiar de ruta', () => {
    const { vm } = crear();
    vm.cargar();
    expect(vm.status()).toBe('ready');
    expect(vm.seleccionado()).toBe(CASO.id);
    expect(vm.caso()?.siniestroId).toBe('SIN-2041');
  });

  it('cola vacía: estado vacío y sin caso abierto', () => {
    const { vm } = crear({ cola: () => of(COLA_VACIA) });
    vm.cargar();
    expect(vm.status()).toBe('empty');
    expect(vm.caso()).toBeNull();
  });

  it('cambiar de chip consulta ese filtro', () => {
    const { vm, llamadas } = crear();
    vm.cargar('rechazados');
    expect(vm.filtro()).toBe('rechazados');
    expect(llamadas).toContain('cola:rechazados');
  });

  it('volver cierra el diálogo sin decidir', () => {
    const { vm, llamadas } = crear();
    vm.cargar();
    vm.abrir('rechazar');
    vm.cerrarDialogo();
    expect(vm.dialogo()).toBeNull();
    expect(llamadas.some((l) => l.startsWith('decidir'))).toBeFalse();
  });

  it('devuelve el foco al control previo al cerrar el diálogo', () => {
    const { vm } = crear();
    vm.cargar();
    const boton = enfocarBoton();

    vm.abrir('aprobar');
    vm.cerrarDialogo();

    expect(document.activeElement).toBe(boton);
    boton.remove();
  });

  it('devuelve el foco al control previo tras confirmar con éxito', () => {
    const { vm } = crear();
    vm.cargar();
    const boton = enfocarBoton();

    vm.abrir('aprobar');
    vm.confirmar('');

    expect(document.activeElement).toBe(boton);
    boton.remove();
  });

  it('no rechaza sin motivo aunque se llame directo', () => {
    const { vm, llamadas } = crear();
    vm.cargar();
    vm.abrir('rechazar');
    vm.confirmar('   ');
    expect(llamadas.some((l) => l.startsWith('decidir'))).toBeFalse();
  });

  it('rechaza con motivo y refresca la cola', () => {
    const { vm, llamadas } = crear();
    vm.cargar();
    vm.abrir('rechazar');
    vm.confirmar('Falta soporte');
    expect(llamadas).toContain('decidir:rechazar:Falta soporte');
    expect(vm.caso()?.estadoCola).toBe('rechazado');
    expect(vm.dialogo()).toBeNull();
    expect(llamadas.filter((l) => l.startsWith('cola')).length).toBe(2);
  });

  it('aprobar un bajo monto encadena con la pantalla de pago', () => {
    const { vm } = crear({}, CASO_BAJO_MONTO);
    vm.cargar();
    vm.abrir('aprobar');
    vm.confirmar('');
    expect(vm.modo()).toBe('pago');
    expect(vm.puedePagar()).toBeTrue();
  });

  it('aprobar un monto alto no abre el pago', () => {
    const { vm } = crear();
    vm.cargar();
    vm.abrir('aprobar');
    vm.confirmar('');
    expect(vm.modo()).toBe('cola');
    expect(vm.puedePagar()).toBeFalse();
  });

  it('enruta a perito', () => {
    const { vm, llamadas } = crear();
    vm.cargar();
    vm.abrir('perito');
    vm.confirmar('Requiere inspección');
    expect(llamadas).toContain('perito:Requiere inspección');
    expect(vm.caso()?.estado).toBe('enrutado');
  });

  it('muestra el rechazo del núcleo (p. ej. caso ya decidido)', () => {
    const { vm } = crear({
      decidir: (): Observable<CasoAviso> =>
        throwError(
          () =>
            new HttpErrorResponse({
              status: 409,
              error: { mensaje: "No se puede pasar de 'decidido'" },
            }),
        ),
    });
    vm.cargar();
    vm.abrir('aprobar');
    vm.confirmar('');
    expect(vm.rechazo()).toContain('decidido');
  });

  it('el reintento de pago devuelve el mismo comprobante y lo marca', () => {
    const pagado: CasoAviso = {
      ...CASO_BAJO_MONTO,
      estado: 'pagado',
      resultado: 'aprobado',
      estadoCola: 'pagado',
      pago: {
        clave_idempotencia: 'idem-1',
        comprobante: 'CMP-1',
        monto: '420000.00',
        origen: 'operador',
        autorizado_por: 'ana',
        pagado_en: '2026-11-02T12:00:00Z',
      },
    };
    const { vm } = crear(
      { pagar: () => of<ResultadoPago>({ pago: pagado.pago!, reintento: true, caso: pagado }) },
      { ...CASO_BAJO_MONTO, estado: 'decidido', resultado: 'aprobado' },
    );
    vm.cargar();
    vm.abrirPago();
    vm.pagar();
    expect(vm.pago()?.reintento).toBeTrue();
    expect(vm.caso()?.pago?.comprobante).toBe('CMP-1');
  });

  it('al refrescar conserva el caso abierto si sigue en el chip', () => {
    let consultas = 0;
    const { vm } = crear({
      caso: () => {
        consultas++;
        return of(CASO);
      },
    });
    vm.cargar();
    vm.cargar();
    expect(consultas).toBe(1);
  });

  it('marca error si no puede abrir el caso o cargar la cola', () => {
    const { vm } = crear({ caso: () => throwError(() => new Error('x')) });
    vm.cargar();
    expect(vm.casoStatus()).toBe('error');

    const otro = crear({ cola: () => throwError(() => new Error('x')) }).vm;
    otro.cargar();
    expect(otro.status()).toBe('error');
  });

  it('ignora confirmar o pagar sin caso abierto', () => {
    const { vm, llamadas } = crear({ cola: () => of(COLA_VACIA) });
    vm.cargar();
    vm.abrir('aprobar');
    vm.confirmar('');
    vm.pagar();
    expect(llamadas.filter((l) => !l.startsWith('cola')).length).toBe(0);
  });

  it('volver a la cola desde el pago', () => {
    const { vm } = crear({}, CASO_BAJO_MONTO);
    vm.cargar();
    vm.abrirPago();
    vm.volverACola();
    expect(vm.modo()).toBe('cola');
    expect(vm.pago()).toBeNull();
  });

  it('muestra el error del pago (técnico o de negocio)', () => {
    const { vm } = crear({ pagar: () => throwError(() => new Error('sin red')) }, CASO_BAJO_MONTO);
    vm.cargar();
    vm.pagar();
    expect(vm.rechazo()).toBe('error');
    expect(vm.enviando()).toBeFalse();
  });

  it('un error técnico al decidir se informa sin cerrar el caso', () => {
    const { vm } = crear({ decidir: () => throwError(() => new Error('sin red')) });
    vm.cargar();
    vm.abrir('aprobar');
    vm.confirmar('');
    expect(vm.rechazo()).toBe('error');
    expect(vm.dialogo()).toBeNull();
  });
});
