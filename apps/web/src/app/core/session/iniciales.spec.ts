import { iniciales } from './iniciales';

describe('iniciales', () => {
  it('toma la primera letra del nombre y del apellido', () => {
    expect(iniciales('Camila', 'Restrepo', 'camila@correo.com')).toBe('CR');
  });

  it('respeta mayusculas aunque el dato venga en minuscula', () => {
    expect(iniciales('camila', 'restrepo', 'camila@correo.com')).toBe('CR');
  });

  it('usa solo el nombre si no hay apellido', () => {
    expect(iniciales('Camila', '', 'camila@correo.com')).toBe('C');
  });

  it('usa solo el apellido si no hay nombre', () => {
    expect(iniciales('', 'Restrepo', 'camila@correo.com')).toBe('R');
  });

  it('cae al correo si no hay nombre ni apellido', () => {
    expect(iniciales('', '', 'camila@correo.com')).toBe('C');
  });

  it('ignora espacios en blanco como si no hubiera dato', () => {
    expect(iniciales('   ', '  ', 'camila@correo.com')).toBe('C');
  });
});
