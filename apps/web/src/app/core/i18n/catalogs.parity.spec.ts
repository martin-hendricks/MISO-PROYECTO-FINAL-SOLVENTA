import esCL from './es-CL.json';
import esCO from './es-CO.json';
import esMX from './es-MX.json';
import esPE from './es-PE.json';

/** Dotted paths of every leaf, e.g. `cotizacion.campo.descripcion.soat`. */
function keys(node: unknown, prefix = ''): string[] {
  if (node === null || typeof node !== 'object') return [prefix];
  return Object.entries(node).flatMap(([k, v]) => keys(v, prefix ? `${prefix}.${k}` : k));
}

/** HU-108: every locale must define the same keys as es-CO. A missing key
 * silently falls back to es-CO text, so the gap would never show as an error. */
describe('i18n catalogs', () => {
  const reference = keys(esCO).sort();

  for (const [locale, catalog] of Object.entries({ 'es-MX': esMX, 'es-CL': esCL, 'es-PE': esPE })) {
    it(`${locale} defines exactly the es-CO keys`, () => {
      const own = keys(catalog).sort();

      expect(reference.filter((k) => !own.includes(k)))
        .withContext(`missing in ${locale}`)
        .toEqual([]);
      expect(own.filter((k) => !reference.includes(k)))
        .withContext(`extra in ${locale}`)
        .toEqual([]);
    });
  }
});
