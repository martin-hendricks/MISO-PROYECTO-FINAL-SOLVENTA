import { HttpErrorResponse } from '@angular/common/http';
import { Observable, of, Subject, throwError } from 'rxjs';
import { Credentials } from '../../core/session/session.service';
import { LoginViewModel } from './login.viewmodel';

function setup(result: Observable<void> = of(undefined)) {
  const signIn = jasmine.createSpy('signIn').and.returnValue(result);
  const onSignedIn = jasmine.createSpy('onSignedIn');
  const viewModel = new LoginViewModel({ signIn }, onSignedIn);
  return { viewModel, signIn, onSignedIn };
}

function fill(viewModel: LoginViewModel, email = 'camila@correo.com', password = 'secreto') {
  viewModel.email.set(email);
  viewModel.password.set(password);
}

describe('LoginViewModel', () => {
  it('starts idle without errors', () => {
    const { viewModel } = setup();

    expect(viewModel.status()).toBe('idle');
    expect(viewModel.failure()).toBeNull();
    expect(viewModel.emailIssue()).toBeNull();
    expect(viewModel.passwordMissing()).toBeFalse();
  });

  it('asks for both fields without calling the session', () => {
    const { viewModel, signIn } = setup();

    viewModel.submit();

    expect(viewModel.emailIssue()).toBe('required');
    expect(viewModel.passwordMissing()).toBeTrue();
    expect(viewModel.status()).toBe('idle');
    expect(signIn).not.toHaveBeenCalled();
  });

  it('rejects a malformed email', () => {
    const { viewModel, signIn } = setup();
    fill(viewModel, 'camila@correo');

    viewModel.submit();

    expect(viewModel.emailIssue()).toBe('format');
    expect(signIn).not.toHaveBeenCalled();
  });

  it('signs in as cliente and reports success', () => {
    const { viewModel, signIn, onSignedIn } = setup();
    fill(viewModel, '  camila@correo.com ');

    viewModel.submit();

    const expected: Credentials = {
      email: 'camila@correo.com',
      password: 'secreto',
      role: 'cliente',
    };
    expect(signIn).toHaveBeenCalledOnceWith(expected);
    expect(onSignedIn).toHaveBeenCalledTimes(1);
    expect(viewModel.status()).toBe('idle');
    expect(viewModel.failure()).toBeNull();
  });

  it('ignores a second submit while the first is in flight', () => {
    const pending = new Subject<void>();
    const { viewModel, signIn } = setup(pending);
    fill(viewModel);

    viewModel.submit();
    viewModel.submit();

    expect(viewModel.status()).toBe('submitting');
    expect(signIn).toHaveBeenCalledTimes(1);
  });

  it('flags invalid credentials on 401 and keeps what was typed', () => {
    const { viewModel, onSignedIn } = setup(
      throwError(() => new HttpErrorResponse({ status: 401 })),
    );
    fill(viewModel);

    viewModel.submit();

    expect(viewModel.status()).toBe('error');
    expect(viewModel.failure()).toBe('credentials');
    expect(viewModel.email()).toBe('camila@correo.com');
    expect(viewModel.password()).toBe('secreto');
    expect(onSignedIn).not.toHaveBeenCalled();
  });

  it('flags a network failure when the BFF is unreachable', () => {
    const { viewModel } = setup(throwError(() => new HttpErrorResponse({ status: 0 })));
    fill(viewModel);

    viewModel.submit();

    expect(viewModel.failure()).toBe('network');
  });

  it('treats an unexpected error as a network failure', () => {
    const { viewModel } = setup(throwError(() => new Error('Token ilegible')));
    fill(viewModel);

    viewModel.submit();

    expect(viewModel.status()).toBe('error');
    expect(viewModel.failure()).toBe('network');
  });

  it('clears the failure when the next attempt is invalid', () => {
    const { viewModel } = setup(throwError(() => new HttpErrorResponse({ status: 401 })));
    fill(viewModel);
    viewModel.submit();

    viewModel.password.set('');
    viewModel.submit();

    expect(viewModel.failure()).toBeNull();
    expect(viewModel.status()).toBe('idle');
    expect(viewModel.passwordMissing()).toBeTrue();
  });
});
