import esCL from '../../core/i18n/es-CL.json';
import esCO from '../../core/i18n/es-CO.json';
import esMX from '../../core/i18n/es-MX.json';
import esPE from '../../core/i18n/es-PE.json';

const CLAVES = [
  'prestadores.title',
  'prestadores.subtitle.cerca',
  'prestadores.usarUbicacion',
  'prestadores.verSiniestro',
  'prestadores.masCercanos',
  'prestadores.comoLlegar',
  'prestadores.bloqueado',
  'prestadores.distancia',
  'prestadores.distanciaEvento',
  'prestadores.claim.pin',
  'prestadores.claim.subtitle',
  'prestadores.claim.sinGeo',
  'prestadores.chip.todos',
  'siniestros.lista.prestadores',
  'siniestros.detalle.prestadores',
  'backoffice.nav.prestadores',
  'backoffice.prestadores.subtitle',
  'backoffice.prestadores.nuevo',
  'backoffice.prestadores.inactivar',
  'backoffice.prestadores.inactivarTitulo',
  'backoffice.prestadores.inactivarCuerpo',
  'backoffice.prestadores.reactivar',
  'backoffice.prestadores.quitarFiltros',
  'backoffice.prestadores.vacio.title',
  'backoffice.prestadores.vacio.body',
  'backoffice.prestadores.error.ramo',
  'backoffice.prestadores.form.guardar',
  'backoffice.prestadores.form.pin',
  'backoffice.prestadores.form.ramosAyuda',
];

function leer(catalogo: Record<string, unknown>, clave: string): unknown {
  return clave.split('.').reduce<unknown>((nodo, parte) => {
    if (nodo && typeof nodo === 'object' && parte in nodo) {
      return (nodo as Record<string, unknown>)[parte];
    }
    return undefined;
  }, catalogo);
}

describe('prestadores catalogs', () => {
  it('has the screen copy in es-CO and the other locales', () => {
    for (const catalogo of [esCO, esMX, esPE, esCL]) {
      for (const clave of CLAVES) {
        expect(typeof leer(catalogo, clave)).withContext(clave).toBe('string');
      }
      expect(leer(esCO, 'backoffice.prestadores.error.ramo')).toBe('Elige al menos un ramo.');
      expect(leer(esCO, 'prestadores.no.existe')).toBeUndefined();
      expect(Object.keys(catalogo.prestadores.tipo).length).toBe(9);
      expect(Object.keys(catalogo.prestadores.ramo).length).toBe(8);
    }
  });
});
