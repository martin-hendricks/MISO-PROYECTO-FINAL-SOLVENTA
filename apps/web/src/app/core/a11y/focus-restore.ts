/** Remembers the focused element before a modal opens and gives it back on
 * close, so keyboard users land where they left off. */
export function capturarFocoActivo(doc: Document = document): HTMLElement | null {
  const activo = doc.activeElement;
  return activo instanceof HTMLElement ? activo : null;
}

export function restaurarFoco(elemento: HTMLElement | null): void {
  if (elemento?.isConnected) {
    elemento.focus();
  }
}
