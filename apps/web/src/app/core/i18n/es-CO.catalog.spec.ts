import esCO from './es-CO.json';

describe('es-CO catalog', () => {
  it('defines the user shell title', () => {
    expect(esCO.shell.user.title).toBe('Portal del cliente');
    expect(esCO.shell.market).toBe('Colombia');
  });
});
