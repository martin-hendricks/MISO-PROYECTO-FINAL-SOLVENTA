import esCO from './es-CO.json';

describe('es-CO catalog', () => {
  it('defines the Inicio title', () => {
    expect(esCO.inicio.title).toBe('Hola');
    expect(esCO.shell.market).toBe('Colombia');
  });
});
