import type { AreaVisible } from '../prestadores.gateway';

export interface ObjetivoCamara {
  lat: number;
  lng: number;
  zoom: number;
}

export const ZOOM_CERCA = 14;

export const MARGEN_TARJETA = 16;

interface Esquina {
  lat: () => number;
  lng: () => number;
}

export function areaDeLimites(limites: {
  getNorthEast: () => Esquina;
  getSouthWest: () => Esquina;
}): AreaVisible {
  const ne = limites.getNorthEast();
  const so = limites.getSouthWest();
  return { norte: ne.lat(), sur: so.lat(), este: ne.lng(), oeste: so.lng() };
}

export function dentroDelArea(area: AreaVisible, punto: { lat: number; lng: number }): boolean {
  return (
    punto.lat <= area.norte &&
    punto.lat >= area.sur &&
    punto.lng <= area.este &&
    punto.lng >= area.oeste
  );
}

/** Pixels to pan down so the card at the bottom of the map stops covering the marker; 0 when it does not. */
export function desplazamientoTarjeta(
  area: AreaVisible,
  lat: number,
  altoMapa: number,
  altoTarjeta: number,
): number {
  const alto = area.norte - area.sur;
  if (alto <= 0 || altoTarjeta <= 0) {
    return 0;
  }
  const y = ((area.norte - lat) / alto) * altoMapa;
  const bordeTarjeta = altoMapa - MARGEN_TARJETA - altoTarjeta;
  return y > bordeTarjeta ? Math.ceil(y - bordeTarjeta + MARGEN_TARJETA) : 0;
}
