import { NEVER, of, throwError } from 'rxjs';
import { ConsentimientoViewModel } from './consentimiento.viewmodel';

describe('ConsentimientoViewModel', () => {
  it('asks for the policy before granting anything', () => {
    const grant = jasmine.createSpy('grant');
    const viewModel = new ConsentimientoViewModel(grant, () => fail('should not continue'));
    expect(viewModel.missing()).toBeFalse();

    viewModel.submit();

    expect(viewModel.missing()).toBeTrue();
    expect(viewModel.status()).toBe('idle');
    expect(grant).not.toHaveBeenCalled();
  });

  it('grants the consent once the policy is accepted', () => {
    const grant = jasmine.createSpy('grant').and.returnValue(of(undefined));
    const onGranted = jasmine.createSpy('onGranted');
    const viewModel = new ConsentimientoViewModel(grant, onGranted);
    viewModel.accepted.set(true);

    viewModel.submit();

    expect(viewModel.missing()).toBeFalse();
    expect(viewModel.status()).toBe('idle');
    expect(grant).toHaveBeenCalledTimes(1);
    expect(onGranted).toHaveBeenCalledTimes(1);
  });

  it('ignores a second attempt while the sign-up is on its way', () => {
    const grant = jasmine.createSpy('grant').and.returnValue(NEVER);
    const viewModel = new ConsentimientoViewModel(grant, () => undefined);
    viewModel.accepted.set(true);

    viewModel.submit();
    viewModel.submit();

    expect(viewModel.status()).toBe('submitting');
    expect(grant).toHaveBeenCalledTimes(1);
  });

  it('stays on consent and lets the customer retry when the sign-up fails', () => {
    const grant = jasmine.createSpy('grant').and.returnValues(
      throwError(() => new Error('caído')),
      of(undefined),
    );
    const onGranted = jasmine.createSpy('onGranted');
    const viewModel = new ConsentimientoViewModel(grant, onGranted);
    viewModel.accepted.set(true);

    viewModel.submit();
    expect(viewModel.status()).toBe('error');
    expect(onGranted).not.toHaveBeenCalled();

    viewModel.submit();
    expect(viewModel.status()).toBe('idle');
    expect(onGranted).toHaveBeenCalledTimes(1);
  });
});
