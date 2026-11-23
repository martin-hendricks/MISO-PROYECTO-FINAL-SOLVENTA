import { HttpErrorResponse } from '@angular/common/http';
import { Observable, of, Subject, throwError } from 'rxjs';
import { Cobertura, PolizaOperador } from './polizas-backoffice.gateway';
import { PolizaBackofficeDetalleViewModel } from './poliza-backoffice-detalle.viewmodel';

const POLIZA: PolizaOperador = {
  numero: 'POL-2026-00000001',
  ramo: 'Protección de dispositivo',
  estado: 'vigente',
  venceEn: '2027-10-01',
  prima: { valor: 1000, periodicidad: 'ANUAL' },
  renovable: true,
  devolucionEstimada: null,
  canceladaEn: null,
  canceladaPor: null,
  motivoCancelacion: null,
  siniestrosAbiertos: null,
  coberturas: [{ nombre: 'Robo', sumaAsegurada: 2000000, deducible: 0 }],
};

function viewModel(
  source: () => Observable<PolizaOperador | null> = () => of(POLIZA),
  renovar: () => Observable<PolizaOperador> = () => of(POLIZA),
  cancelar: (motivo: string) => Observable<PolizaOperador> = () => of(POLIZA),
  modificarCoberturas: (coberturas: Cobertura[]) => Observable<PolizaOperador> = () => of(POLIZA),
) {
  return new PolizaBackofficeDetalleViewModel(source, renovar, cancelar, modificarCoberturas);
}

describe('PolizaBackofficeDetalleViewModel', () => {
  it('stays loading until the BFF answers', () => {
    const pending = new Subject<PolizaOperador | null>();
    const vm = viewModel(() => pending);

    vm.load();

    expect(vm.status()).toBe('loading');
  });

  it('shows the policy the BFF returns', () => {
    const vm = viewModel();

    vm.load();

    expect(vm.status()).toBe('ready');
    expect(vm.poliza()).toEqual(POLIZA);
  });

  it('reports a missing policy as not found', () => {
    const vm = viewModel(() => of(null));

    vm.load();

    expect(vm.status()).toBe('not-found');
  });

  it('a load failure is a retryable error', () => {
    const vm = viewModel(() => throwError(() => new Error('sin red')));

    vm.load();

    expect(vm.status()).toBe('error');
  });

  it('renovar updates the policy and marks the action done', () => {
    const renovada: PolizaOperador = { ...POLIZA, venceEn: '2028-10-01' };
    const vm = viewModel(() => of(POLIZA), () => of(renovada));
    vm.load();

    vm.renovar();

    expect(vm.accion()).toBe('hecho');
    expect(vm.poliza()).toEqual(renovada);
  });

  it('cancelar sends the reason and marks the action done', () => {
    const cancelada: PolizaOperador = { ...POLIZA, estado: 'cancelada' };
    let motivoEnviado: string | undefined;
    const vm = viewModel(
      () => of(POLIZA),
      () => of(POLIZA),
      (motivo) => {
        motivoEnviado = motivo;
        return of(cancelada);
      },
    );
    vm.load();

    vm.cancelar('El cliente lo pidió');

    expect(motivoEnviado).toBe('El cliente lo pidió');
    expect(vm.accion()).toBe('hecho');
    expect(vm.poliza()).toEqual(cancelada);
  });

  it('a 409 business rejection on cancelar surfaces its message without a generic error', () => {
    const error = new HttpErrorResponse({
      status: 409,
      error: { codigo: 'ya_cancelada', mensaje: 'La póliza ya estaba cancelada' },
    });
    const vm = viewModel(
      () => of(POLIZA),
      () => of(POLIZA),
      () => throwError(() => error),
    );
    vm.load();

    vm.cancelar('Otro motivo');

    expect(vm.accion()).toBe('rechazado');
    expect(vm.rechazo()).toBe('La póliza ya estaba cancelada');
  });

  it('a 409 business rejection on renovar surfaces its message', () => {
    const error = new HttpErrorResponse({
      status: 409,
      error: { codigo: 'transicion_invalida', mensaje: 'No renovable' },
    });
    const vm = viewModel(
      () => of(POLIZA),
      () => throwError(() => error),
    );
    vm.load();

    vm.renovar();

    expect(vm.accion()).toBe('rechazado');
    expect(vm.rechazo()).toBe('No renovable');
  });

  it('a non-business error on renovar goes back to idle, not rechazado', () => {
    const vm = viewModel(
      () => of(POLIZA),
      () => throwError(() => new Error('sin red')),
    );
    vm.load();

    vm.renovar();

    expect(vm.accion()).toBe('idle');
    expect(vm.rechazo()).toBeNull();
  });

  it('a non-business error on cancelar goes back to idle, not rechazado', () => {
    const vm = viewModel(
      () => of(POLIZA),
      () => of(POLIZA),
      () => throwError(() => new Error('sin red')),
    );
    vm.load();

    vm.cancelar('El cliente lo pidió');

    expect(vm.accion()).toBe('idle');
    expect(vm.rechazo()).toBeNull();
  });

  it('modificarCoberturas sends the new coverages and marks the action done', () => {
    const nuevasCoberturas: Cobertura[] = [{ nombre: 'Pantalla', sumaAsegurada: 500000, deducible: 50000 }];
    const modificada: PolizaOperador = { ...POLIZA, coberturas: nuevasCoberturas };
    let coberturasEnviadas: Cobertura[] | undefined;
    const vm = viewModel(
      () => of(POLIZA),
      () => of(POLIZA),
      () => of(POLIZA),
      (coberturas) => {
        coberturasEnviadas = coberturas;
        return of(modificada);
      },
    );
    vm.load();

    vm.modificarCoberturas(nuevasCoberturas);

    expect(coberturasEnviadas).toEqual(nuevasCoberturas);
    expect(vm.accion()).toBe('hecho');
    expect(vm.poliza()).toEqual(modificada);
  });

  it('a 409 business rejection on modificarCoberturas surfaces its message', () => {
    const error = new HttpErrorResponse({
      status: 422,
      error: { codigo: 'cobertura_invalida', mensaje: 'Suma asegurada inválida' },
    });
    const vm = viewModel(
      () => of(POLIZA),
      () => of(POLIZA),
      () => of(POLIZA),
      () => throwError(() => error),
    );
    vm.load();

    vm.modificarCoberturas([{ nombre: 'Robo', sumaAsegurada: -1, deducible: 0 }]);

    expect(vm.accion()).toBe('rechazado');
    expect(vm.rechazo()).toBe('Suma asegurada inválida');
  });

  it('a non-business error on modificarCoberturas goes back to idle, not rechazado', () => {
    const vm = viewModel(
      () => of(POLIZA),
      () => of(POLIZA),
      () => of(POLIZA),
      () => throwError(() => new Error('sin red')),
    );
    vm.load();

    vm.modificarCoberturas([{ nombre: 'Robo', sumaAsegurada: 1000, deducible: 0 }]);

    expect(vm.accion()).toBe('idle');
    expect(vm.rechazo()).toBeNull();
  });
});
