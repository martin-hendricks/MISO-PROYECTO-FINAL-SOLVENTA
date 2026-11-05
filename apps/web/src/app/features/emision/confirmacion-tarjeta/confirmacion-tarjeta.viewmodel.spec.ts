import { ConfirmacionTarjetaViewModel } from './confirmacion-tarjeta.viewmodel';

describe('ConfirmacionTarjetaViewModel', () => {
  it('keeps confirmation unavailable until every local field is valid', () => {
    const vm = new ConfirmacionTarjetaViewModel();
    expect(vm.ready()).toBeFalse();
    vm.setHolder('Camila Restrepo');
    vm.setNumber('4242424242424242');
    vm.setMonth('8');
    vm.setYear('28');
    vm.setCode('12');
    expect(vm.month()).toBe('08');
    expect(vm.ready()).toBeFalse();
    vm.setCode('123');
    expect(vm.ready()).toBeTrue();
    expect(vm.numberHint()).toBe('tarjeta.numeroHint.default');
    vm.setNumber('378282246310005');
    expect(vm.numberHint()).toBe('tarjeta.numeroHint.amex');
    vm.setNumber('30569309025904');
    expect(vm.numberHint()).toBe('tarjeta.numeroHint.diners');
  });

  it('discards every card value when the customer leaves', () => {
    const vm = new ConfirmacionTarjetaViewModel();
    vm.setHolder('Camila');
    vm.setNumber('4242424242424242');
    vm.clear();
    expect(vm.holder()).toBe('');
    expect(vm.number()).toBe('');
  });
});
