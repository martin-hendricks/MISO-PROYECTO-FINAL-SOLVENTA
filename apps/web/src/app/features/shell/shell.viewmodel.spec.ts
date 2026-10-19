import { ShellViewModel } from './shell.viewmodel';

describe('ShellViewModel', () => {
  it('starts idle and becomes ready when activated', () => {
    const viewModel = new ShellViewModel();

    expect(viewModel.status()).toBe('idle');

    viewModel.activate();

    expect(viewModel.status()).toBe('ready');
  });
});
