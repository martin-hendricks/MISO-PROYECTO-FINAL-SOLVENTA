import type { Cluster, Renderer } from '@angular/google-maps';
import {
  defaultOnClusterClickHandler,
  MarkerClusterer,
  SuperClusterAlgorithm,
} from '@googlemaps/markerclusterer';

export interface Punto {
  lat: number;
  lng: number;
}

/** Providers that share a coordinate stay one marker at every zoom. */
export interface GrupoCoincidente<T extends Punto> {
  lat: number;
  lng: number;
  prestadores: T[];
}

export const OPCIONES_AGRUPACION = { radius: 60, maxZoom: 13 } as const;

export const ALGORITMO = new SuperClusterAlgorithm({ ...OPCIONES_AGRUPACION });

export const COLOR_GRUPO = '#006a6a';

const RADIO_TIERRA_M = 6_371_000;

export function distanciaMetros(a: Punto, b: Punto): number {
  const rad = Math.PI / 180;
  const dLat = (b.lat - a.lat) * rad;
  const dLng = (b.lng - a.lng) * rad;
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLng / 2) ** 2;
  return 2 * RADIO_TIERRA_M * Math.asin(Math.sqrt(h));
}

/** Measured against the first member of each stack, so the order of the answer decides the anchor. */
export function apilarCoincidentes<T extends Punto>(
  prestadores: readonly T[],
  metros = 10,
): GrupoCoincidente<T>[] {
  const grupos: GrupoCoincidente<T>[] = [];
  for (const prestador of prestadores) {
    const grupo = grupos.find((candidato) => distanciaMetros(candidato, prestador) < metros);
    if (grupo) {
      grupo.prestadores.push(prestador);
    } else {
      grupos.push({ lat: prestador.lat, lng: prestador.lng, prestadores: [prestador] });
    }
  }
  return grupos;
}

export function tamanoGrupo(n: number): number {
  if (n <= 9) {
    return 40;
  }
  return n <= 49 ? 48 : 56;
}

function circulo(tamano: number): string {
  const r = tamano / 2;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${tamano}" height="${tamano}"><circle cx="${r}" cy="${r}" r="${r - 2}" fill="${COLOR_GRUPO}" stroke="#ffffff" stroke-width="3"/></svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

export class RenderizadorGrupos implements Renderer {
  constructor(private readonly titulo: (n: number) => string) {}

  render({ count, position }: Cluster): google.maps.Marker {
    const tamano = tamanoGrupo(count);
    return new google.maps.Marker({
      position,
      title: this.titulo(count),
      label: { text: String(count), color: '#ffffff', fontSize: '14px', fontWeight: '600' },
      icon: {
        url: circulo(tamano),
        scaledSize: new google.maps.Size(tamano, tamano),
        anchor: new google.maps.Point(tamano / 2, tamano / 2),
      },
      zIndex: Number(google.maps.Marker.MAX_ZINDEX) + count,
    });
  }
}

/** `MapMarkerClusterer` reads the library from the `markerClusterer` global of its UMD build. */
export function registrarAgrupador(): void {
  (globalThis as { markerClusterer?: unknown }).markerClusterer = {
    MarkerClusterer,
    defaultOnClusterClickHandler,
  };
}
