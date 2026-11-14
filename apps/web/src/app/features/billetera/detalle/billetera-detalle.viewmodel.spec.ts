import { of, throwError } from 'rxjs';
import { ASISTIDO, AUTOMATICO } from '../billetera.testing';
import { BilleteraDetalleViewModel } from './billetera-detalle.viewmodel';

describe('BilleteraDetalleViewModel', () => {
  it('opens the claim for an assisted deposit and the automatic payment view otherwise', () => {
    const asistido = new BilleteraDetalleViewModel(() => of(ASISTIDO));
    asistido.load();
    expect(asistido.status()).toBe('ready');
    expect(asistido.destinoSiniestro(ASISTIDO)).toBe(`/siniestros/${ASISTIDO.id}`);
    expect(new BilleteraDetalleViewModel(() => of(AUTOMATICO)).destinoSiniestro(AUTOMATICO)).toBe(
      '/siniestros/parametrico',
    );
  });

  it('is not-found on null and error when the read fails', () => {
    const ausente = new BilleteraDetalleViewModel(() => of(null));
    ausente.load();
    expect(ausente.status()).toBe('notFound');
    const caido = new BilleteraDetalleViewModel(() => throwError(() => new Error('caido')));
    caido.load();
    expect(caido.status()).toBe('error');
  });
});
