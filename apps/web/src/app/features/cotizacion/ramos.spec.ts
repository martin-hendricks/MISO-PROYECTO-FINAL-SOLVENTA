import { datosRiesgo, ramoPorId } from './ramos';

describe('ramos', () => {
  it('types the risk data of a line and sends empty text for a missing value', () => {
    const dispositivo = ramoPorId('dispositivo')!;

    expect(datosRiesgo(dispositivo, { valorDispositivo: '2400000', masDe12Meses: 'si' })).toEqual({
      valorDispositivo: 2400000,
      marca: '',
      modelo: '',
      masDe12Meses: true,
    });
  });
});
