import { capturarFocoActivo, restaurarFoco } from './focus-restore';

describe('focus-restore', () => {
  let anterior: HTMLElement | null = null;

  afterEach(() => {
    anterior?.remove();
    anterior = null;
    (document.activeElement as HTMLElement | null)?.blur?.();
  });

  function montarBoton(): HTMLButtonElement {
    const boton = document.createElement('button');
    document.body.appendChild(boton);
    boton.focus();
    return boton;
  }

  it('returns the focused element', () => {
    const boton = montarBoton();
    anterior = boton;

    expect(capturarFocoActivo()).toBe(boton);
  });

  it('returns null when activeElement is not an HTMLElement', () => {
    const falso = { activeElement: null } as unknown as Document;

    expect(capturarFocoActivo(falso)).toBeNull();
  });

  it('restores focus to a connected element', () => {
    const boton = montarBoton();
    anterior = boton;
    const otro = document.createElement('button');
    document.body.appendChild(otro);
    otro.focus();
    expect(document.activeElement).toBe(otro);

    restaurarFoco(boton);

    expect(document.activeElement).toBe(boton);
    otro.remove();
  });

  it('ignores a detached element', () => {
    const boton = document.createElement('button');
    boton.focus();
    expect(document.activeElement).not.toBe(boton);

    restaurarFoco(boton);

    expect(document.activeElement).not.toBe(boton);
  });

  it('accepts null', () => {
    expect(() => restaurarFoco(null)).not.toThrow();
  });
});
