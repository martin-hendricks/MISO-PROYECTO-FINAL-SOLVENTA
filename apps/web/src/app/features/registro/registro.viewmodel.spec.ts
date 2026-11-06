import { Alta } from './registro.draft';
import { RegistroViewModel } from './registro.viewmodel';

describe('RegistroViewModel', () => {
  function fill(viewModel: RegistroViewModel, alta: Partial<Alta> = {}): void {
    viewModel.nombre.set(alta.nombre ?? 'Camila');
    viewModel.apellidos.set(alta.apellidos ?? 'Restrepo');
    viewModel.documento.set(alta.documento ?? '1012345678');
    viewModel.correo.set(alta.correo ?? 'camila@correo.com');
    viewModel.contrasena.set(alta.contrasena ?? 'secreto123');
    viewModel.setIncome('4500000');
    viewModel.setSpending('1200000');
  }

  it('shows no issue before the first attempt', () => {
    const viewModel = new RegistroViewModel(() => fail('should not continue'));

    expect(viewModel.issues()).toEqual({});
  });

  it('continues with the trimmed data and no camera step', () => {
    const onContinue = jasmine.createSpy('onContinue');
    const viewModel = new RegistroViewModel(onContinue);
    fill(viewModel, { nombre: '  Camila ', correo: ' camila@correo.com ' });

    viewModel.submit();

    expect(viewModel.issues()).toEqual({});
    expect(onContinue).toHaveBeenCalledOnceWith({
      nombre: 'Camila',
      apellidos: 'Restrepo',
      documento: '1012345678',
      correo: 'camila@correo.com',
      contrasena: 'secreto123',
      ingresos_mensuales: '4500000.00',
      gastos_mensuales: '1200000.00',
    });
  });

  it('asks for every field left blank', () => {
    const onContinue = jasmine.createSpy('onContinue');
    const viewModel = new RegistroViewModel(onContinue);

    viewModel.submit();

    expect(viewModel.issues()).toEqual({
      nombre: 'required',
      apellidos: 'required',
      documento: 'required',
      correo: 'required',
      contrasena: 'required',
      ingresos_mensuales: 'required',
      gastos_mensuales: 'required',
    });
    expect(onContinue).not.toHaveBeenCalled();
  });

  it('rejects a malformed email and a short password', () => {
    const onContinue = jasmine.createSpy('onContinue');
    const viewModel = new RegistroViewModel(onContinue);
    fill(viewModel, { correo: 'camila@correo', contrasena: 'corta' });

    viewModel.submit();

    expect(viewModel.issues()).toEqual({ correo: 'format', contrasena: 'length' });
    expect(onContinue).not.toHaveBeenCalled();
  });

  it('groups COP amounts and blocks income that is not greater than zero', () => {
    const onContinue = jasmine.createSpy('onContinue');
    const viewModel = new RegistroViewModel(onContinue);
    fill(viewModel);
    viewModel.setIncome('$4.500.000');
    viewModel.setSpending('0');

    expect(viewModel.incomeDisplay()).toBe('$4.500.000');
    expect(viewModel.spendingDisplay()).toBe('$0');
    viewModel.submit();
    expect(onContinue).toHaveBeenCalledOnceWith(
      jasmine.objectContaining({ ingresos_mensuales: '4500000.00', gastos_mensuales: '0.00' }),
    );

    viewModel.setIncome('0');
    viewModel.submit();
    expect(viewModel.issues().ingresos_mensuales).toBe('amount');
  });

  it('clears the issue once the field is fixed', () => {
    const viewModel = new RegistroViewModel(() => undefined);
    fill(viewModel, { documento: ' ' });
    viewModel.submit();
    expect(viewModel.issues().documento).toBe('required');

    viewModel.documento.set('1012345678');

    expect(viewModel.issues()).toEqual({});
  });
});
