import { of, Subject, throwError } from 'rxjs';
import { DifusionEntrada } from './notificaciones.gateway';
import { AUDIENCIA, HISTORIAL, RESULTADO } from './notificaciones.testing';
import { LIMITE_CUERPO, LIMITE_TITULO, NotificacionesViewModel, PuertosNotificaciones } from './notificaciones.viewmodel';

describe('NotificacionesViewModel', () => {
  function crear() {
    const envios: DifusionEntrada[] = [];
    let historiales = 0;
    const puertos: PuertosNotificaciones = {
      audiencia: () => of({ usuarios: AUDIENCIA }),
      enviar: (body) => {
        envios.push(body);
        return of(RESULTADO);
      },
      historial: () => {
        historiales += 1;
        return of({ items: HISTORIAL });
      },
    };
    return { vm: new NotificacionesViewModel(puertos), envios, lecturas: () => historiales };
  }

  it('counts the characters left under the title and body limits', () => {
    const { vm } = crear();
    expect(vm.restantesTitulo()).toBe(LIMITE_TITULO);
    expect(vm.restantesCuerpo()).toBe(LIMITE_CUERPO);

    vm.titulo.set('Aviso');
    vm.cuerpo.set('x'.repeat(LIMITE_CUERPO + 1));

    expect(vm.restantesTitulo()).toBe(LIMITE_TITULO - 'Aviso'.length);
    expect(vm.restantesCuerpo()).toBe(-1);
    expect(vm.puedeEnviar()).toBeFalse();
  });

  it('disables send when the message is empty or the chosen audience is empty', () => {
    const { vm } = crear();
    expect(vm.puedeEnviar()).toBeFalse();

    vm.titulo.set('Aviso');
    vm.cuerpo.set('Texto');
    expect(vm.puedeEnviar()).toBeTrue();

    vm.elegirModo('usuarios');
    expect(vm.puedeEnviar()).toBeFalse();
    vm.alternar(AUDIENCIA[0].usuarioId);
    expect(vm.puedeEnviar()).toBeTrue();
    expect(vm.etiqueta(AUDIENCIA[0])).toBe('Ana Ruiz · 1020334556');
    expect(vm.persona(AUDIENCIA[0])).toBe('Ana Ruiz');
    expect(vm.documento(AUDIENCIA[0])).toBe('1020334556');
    expect(vm.etiqueta({ ...AUDIENCIA[0], nombre: ' ', apellidos: '' })).toBe(
      'ana@correo.com · 1020334556',
    );
    expect(
      vm.etiqueta({
        ...AUDIENCIA[0],
        email: undefined as unknown as string,
        documento: undefined as unknown as string,
      }),
    ).toBe('Ana Ruiz');
  });

  it('mirrors the inputs in the preview', () => {
    const { vm } = crear();
    vm.titulo.set('  Mantenimiento');
    vm.cuerpo.set('El domingo');
    expect(vm.vistaPrevia()).toEqual({ titulo: '  Mantenimiento', cuerpo: 'El domingo' });
  });

  it('shows the result counts and reloads the history after sending', () => {
    const { vm, envios, lecturas } = crear();
    vm.cargar();
    const antes = lecturas();

    vm.titulo.set('Aviso');
    vm.cuerpo.set('Texto');
    vm.poliza.set('POL-1');
    vm.enviar();

    expect(envios[0]).toEqual({
      titulo: 'Aviso',
      cuerpo: 'Texto',
      audiencia: { tipo: 'todos' },
      poliza: 'POL-1',
    });
    expect(vm.resultado()).toEqual(RESULTADO);
    expect(lecturas()).toBe(antes + 1);
    expect(vm.historial()).toEqual(HISTORIAL);
  });

  it('sends a chosen audience without a policy and reports a failed send', () => {
    const envios: DifusionEntrada[] = [];
    const vm = new NotificacionesViewModel({
      audiencia: () => of({ usuarios: AUDIENCIA }),
      historial: () => of({ items: [] }),
      enviar: (body) => {
        envios.push(body);
        return throwError(() => new Error('caído'));
      },
    });
    vm.cargar();
    vm.titulo.set('Aviso');
    vm.cuerpo.set('Texto');
    vm.elegirModo('usuarios');
    vm.enviar();
    expect(envios).toEqual([]);
    vm.alternar(AUDIENCIA[0].usuarioId);
    vm.alternar(AUDIENCIA[0].usuarioId);
    vm.enviar();
    expect(envios).toEqual([]);
    vm.alternar(AUDIENCIA[0].usuarioId);
    vm.enviar();
    expect(envios[0].audiencia).toEqual({ tipo: 'usuarios', usuarioIds: [AUDIENCIA[0].usuarioId] });
    expect(envios[0].poliza).toBeUndefined();
    expect(vm.errorEnvio()).toBeTrue();
  });

  it('reports a history reload failure after a successful send', () => {
    let historiales = 0;
    const vm = new NotificacionesViewModel({
      audiencia: () => of({ usuarios: [] }),
      historial: () => {
        historiales += 1;
        return historiales === 1 ? of({ items: [] }) : throwError(() => new Error('caído'));
      },
      enviar: () => of(RESULTADO),
    });
    vm.cargar();
    vm.titulo.set('Aviso');
    vm.cuerpo.set('Texto');
    vm.enviar();
    expect(vm.resultado()).toEqual(RESULTADO);
    expect(vm.status()).toBe('error');
  });

  it('uses the email when the legal name is missing and reports a failed load', () => {
    const { vm } = crear();
    const sinNombre = {
      ...AUDIENCIA[0],
      nombre: undefined as unknown as string,
      apellidos: null as unknown as string,
      email: undefined as unknown as string,
    };
    expect(vm.persona(sinNombre)).toBe('');
    expect(vm.documento({ ...sinNombre, documento: null as unknown as string })).toBe('');

    const caido = new NotificacionesViewModel({
      audiencia: () => throwError(() => new Error('caído')),
      historial: () => of({ items: [] }),
      enviar: () => of(RESULTADO),
    });
    caido.cargar();
    expect(caido.status()).toBe('error');
  });

  it('stays loading until both reads answer', () => {
    const audiencia = new Subject<{ usuarios: typeof AUDIENCIA }>();
    const historial = new Subject<{ items: typeof HISTORIAL }>();
    const vm = new NotificacionesViewModel({
      audiencia: () => audiencia,
      historial: () => historial,
      enviar: () => of(RESULTADO),
    });

    vm.cargar();
    expect(vm.status()).toBe('loading');
    audiencia.next({ usuarios: AUDIENCIA });
    expect(vm.status()).toBe('loading');
    historial.next({ items: HISTORIAL });
    audiencia.complete();
    historial.complete();
    expect(vm.status()).toBe('ready');
    expect(vm.audiencia()).toEqual(AUDIENCIA);
  });
});
