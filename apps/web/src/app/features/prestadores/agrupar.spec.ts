import { SuperClusterAlgorithm } from '@googlemaps/markerclusterer';
import { PRESTADOR } from './prestadores.testing';
import {
  ALGORITMO,
  apilarCoincidentes,
  COLOR_GRUPO,
  distanciaMetros,
  OPCIONES_AGRUPACION,
  registrarAgrupador,
  RenderizadorGrupos,
  tamanoGrupo,
} from './agrupar';
import { iconoPin } from './tipo-prestador';

type Global = { google?: unknown; markerClusterer?: unknown };

class MarcadorFalso {
  static readonly MAX_ZINDEX = 1000;
  constructor(readonly opciones: Record<string, unknown>) {}
}

class Medida {
  constructor(
    readonly x: number,
    readonly y: number,
  ) {}
}

describe('apilarCoincidentes', () => {
  it('stacks providers less than 10 m apart and keeps the others apart', () => {
    const vecino = { ...PRESTADOR, id: 'PRE-A', lat: PRESTADOR.lat + 0.00005 };
    const lejano = { ...PRESTADOR, id: 'PRE-B', lat: PRESTADOR.lat + 0.0002 };
    const grupos = apilarCoincidentes([PRESTADOR, lejano, vecino], 10);

    expect(distanciaMetros(PRESTADOR, vecino)).toBeLessThan(10);
    expect(distanciaMetros(PRESTADOR, lejano)).toBeGreaterThan(10);
    expect(grupos.map((grupo) => grupo.prestadores.map((p) => p.id))).toEqual([
      ['PRE-BOG-06', 'PRE-A'],
      ['PRE-B'],
    ]);
    expect(grupos[0].lat).toBe(PRESTADOR.lat);
    expect(apilarCoincidentes([])).toEqual([]);
  });
});

describe('cluster options and renderer', () => {
  const global = globalThis as unknown as Global;

  beforeEach(() => {
    global.google = { maps: { Marker: MarcadorFalso, Size: Medida, Point: Medida } };
  });

  afterEach(() => {
    delete global.google;
    delete global.markerClusterer;
  });

  it('groups with a 60 px radius only up to zoom 13', () => {
    expect(OPCIONES_AGRUPACION).toEqual({ radius: 60, maxZoom: 13 });
    expect(ALGORITMO).toBeInstanceOf(SuperClusterAlgorithm);
  });

  it('draws a teal circle in three sizes with the count and the accessible title', () => {
    const titulos: number[] = [];
    const renderizador = new RenderizadorGrupos((n) => {
      titulos.push(n);
      return `${n} prestadores, toca para acercar`;
    });
    const posicion = { lat: () => 4.6, lng: () => -74.06 };
    const marcar = (count: number) =>
      (
        renderizador.render({ count, position: posicion } as never) as unknown as MarcadorFalso
      ).opciones;

    const chico = marcar(9);
    const medio = marcar(10);
    const grande = marcar(50);

    expect([9, 10, 49, 50].map(tamanoGrupo)).toEqual([40, 48, 48, 56]);
    expect(chico['title']).toBe('9 prestadores, toca para acercar');
    expect(chico['label']).toEqual(jasmine.objectContaining({ text: '9' }));
    expect(chico['position']).toBe(posicion);
    expect(chico['zIndex']).toBe(1009);
    const icono = chico['icon'] as { url: string; scaledSize: Medida; anchor: Medida };
    expect(decodeURIComponent(icono.url)).toContain(COLOR_GRUPO);
    expect(icono.scaledSize).toEqual(new Medida(40, 40));
    expect(icono.anchor).toEqual(new Medida(20, 20));
    expect((medio['icon'] as { scaledSize: Medida }).scaledSize.x).toBe(48);
    expect((grande['icon'] as { scaledSize: Medida }).scaledSize.x).toBe(56);
    expect(titulos).toEqual([9, 10, 50]);
  });

  it('exposes the clusterer to @angular/google-maps through the global it reads', () => {
    registrarAgrupador();
    const registrado = global.markerClusterer as Record<string, unknown>;
    expect(typeof registrado['MarkerClusterer']).toBe('function');
    expect(typeof registrado['defaultOnClusterClickHandler']).toBe('function');
  });
});

describe('iconoPin', () => {
  it('keeps the type color and draws the chosen marker larger', () => {
    expect(iconoPin('grua')).toEqual(jasmine.objectContaining({ fillColor: '#6a1b9a', scale: 9 }));
    expect(iconoPin('grua', true)).toEqual(jasmine.objectContaining({ scale: 13, strokeWeight: 2 }));
  });
});
