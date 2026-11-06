import { of } from 'rxjs';
import { PagoParametrico } from '../siniestros.gateway';
import { ParametricoViewModel } from './parametrico.viewmodel';

const PAGO: PagoParametrico = {
  siniestroId: 'SIN-220',
  poliza: 'POL-77310',
  umbral: '≥ 80 mm / 24 h',
  monto: 1200000,
  moneda: 'COP',
  estado: 'pagado',
};

describe('ParametricoViewModel', () => {
  it('loads the stored payout and updates only the related policy preference', () => {
    const saved: boolean[] = [];
    const vm = new ParametricoViewModel(
      () => of(PAGO),
      (_numero, enabled) => {
        saved.push(enabled);
        return of({ numero: PAGO.poliza, renovacionAutomatica: enabled });
      },
    );

    expect(vm.renewal()).toBeFalse();
    vm.chooseRenewal(true);
    expect(saved).toEqual([]);
    vm.open();
    expect(vm.pago()).toEqual(PAGO);
    vm.chooseRenewal(true);
    expect(saved).toEqual([true]);
  });
});
