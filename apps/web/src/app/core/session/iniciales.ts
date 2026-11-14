/** Iniciales para el avatar del usuario logueado (shell cliente y back-office).
 * Primera letra del nombre y del primer apellido; si falta alguno, usa lo que
 * haya. Sin nombre/apellidos, cae al correo (igual que `nombreCliente` en
 * backoffice/clientes/clientes.viewmodel.ts). */
export function iniciales(nombre: string, apellidos: string, correo: string): string {
  const partes = [nombre.trim(), apellidos.trim()].filter(Boolean);
  if (partes.length === 0) {
    return correo.trim().charAt(0).toUpperCase();
  }
  return partes
    .slice(0, 2)
    .map((parte) => parte.charAt(0).toUpperCase())
    .join('');
}
