import { of, Subject, throwError } from 'rxjs';
import { ConsentimientoPerfil } from './consentimiento-perfil.gateway';
import { ConsentimientoPerfilViewModel } from './consentimiento-perfil.viewmodel';

describe('ConsentimientoPerfilViewModel', () => {
  const VIGENTE: ConsentimientoPerfil = { estado: 'vigente', otorgadoEn: '2026-10-01T10:00:00Z' };
  const REVOCADO: ConsentimientoPerfil = { estado: 'revocado', revocadoEn: '2026-11-11T15:30:00Z' };

  function crear(carga = of(VIGENTE), revocacion = of(REVOCADO)) {
    const revocar = jasmine.createSpy('revocar').and.returnValue(revocacion);
    const vm = new ConsentimientoPerfilViewModel(() => carga, revocar);
    vm.load();
    return { vm, revocar };
  }

  it('exposes the grant date when the consent is in force', () => {
    const { vm } = crear();

    expect(vm.vigente()).toBeTrue();
    expect(vm.otorgadoEn()).toBe('2026-10-01T10:00:00Z');
    expect(vm.revocadoEn()).toBeNull();
  });

  it('has no dates when the customer never granted the consent', () => {
    const { vm } = crear(of({ estado: 'sin_consentimiento' }));

    expect(vm.cargado()).toBeTrue();
    expect(vm.vigente()).toBeFalse();
    expect(vm.otorgadoEn()).toBeNull();
    expect(vm.revocadoEn()).toBeNull();
  });

  it('is not in force when the consent cannot be read', () => {
    const { vm } = crear(throwError(() => new Error('503')));

    expect(vm.cargado()).toBeFalse();
    expect(vm.vigente()).toBeFalse();
  });

  it('opens and closes the dialog without revoking', () => {
    const { vm, revocar } = crear();

    vm.abrir();
    expect(vm.dialogo()).toBeTrue();
    vm.cerrar();

    expect(vm.dialogo()).toBeFalse();
    expect(revocar).not.toHaveBeenCalled();
    expect(vm.otorgadoEn()).toBe('2026-10-01T10:00:00Z');
  });

  it('revokes, closes the dialog and keeps the revocation date', () => {
    const { vm, revocar } = crear();

    vm.abrir();
    vm.revocar();

    expect(revocar).toHaveBeenCalledTimes(1);
    expect(vm.dialogo()).toBeFalse();
    expect(vm.vigente()).toBeFalse();
    expect(vm.revocadoEn()).toBe('2026-11-11T15:30:00Z');
    expect(vm.otorgadoEn()).toBeNull();
    expect(vm.error()).toBeFalse();
  });

  it('ignores a second revoke while the first one is in flight', () => {
    const enCurso = new Subject<ConsentimientoPerfil>();
    const { vm, revocar } = crear(of(VIGENTE), enCurso);

    vm.abrir();
    vm.revocar();
    vm.revocar();

    expect(revocar).toHaveBeenCalledTimes(1);
    expect(vm.revocando()).toBeTrue();
  });

  it('keeps the consent in force and reports the failure when revoking fails', () => {
    const { vm } = crear(
      of(VIGENTE),
      throwError(() => new Error('503')),
    );

    vm.abrir();
    vm.revocar();

    expect(vm.dialogo()).toBeFalse();
    expect(vm.error()).toBeTrue();
    expect(vm.revocando()).toBeFalse();
    expect(vm.otorgadoEn()).toBe('2026-10-01T10:00:00Z');
  });

  it('is no longer in force when the core reports nothing left to revoke', () => {
    const { vm } = crear(of(VIGENTE), of({ estado: 'sin_consentimiento' }));

    vm.abrir();
    vm.revocar();

    expect(vm.vigente()).toBeFalse();
  });
});
