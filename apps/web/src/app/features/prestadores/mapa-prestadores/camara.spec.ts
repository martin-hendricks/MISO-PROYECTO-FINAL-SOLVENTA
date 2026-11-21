import { AREA_CHAPINERO } from '../prestadores.testing';
import { areaConSuperficie, areaDeLimites, dentroDelArea, desplazamientoTarjeta } from './camara';

describe('camara', () => {
  it('reads the visible area from the map bounds', () => {
    const esquina = (lat: number, lng: number) => ({ lat: () => lat, lng: () => lng });
    expect(
      areaDeLimites({
        getNorthEast: () => esquina(4.66, -74.05),
        getSouthWest: () => esquina(4.62, -74.08),
      }),
    ).toEqual(AREA_CHAPINERO);
  });

  it('tells an area with surface from one whose map has no size', () => {
    expect(areaConSuperficie(AREA_CHAPINERO)).toBeTrue();
    expect(areaConSuperficie({ ...AREA_CHAPINERO, sur: AREA_CHAPINERO.norte })).toBeFalse();
    expect(areaConSuperficie({ ...AREA_CHAPINERO, oeste: AREA_CHAPINERO.este })).toBeFalse();
    expect(areaConSuperficie({ norte: 4.6, sur: 4.7, este: -74.05, oeste: -74.08 })).toBeFalse();
  });

  it('tells whether a provider is inside the area', () => {
    expect(dentroDelArea(AREA_CHAPINERO, { lat: 4.64, lng: -74.06 })).toBeTrue();
    expect(dentroDelArea(AREA_CHAPINERO, { lat: 4.7, lng: -74.06 })).toBeFalse();
    expect(dentroDelArea(AREA_CHAPINERO, { lat: 4.6, lng: -74.06 })).toBeFalse();
    expect(dentroDelArea(AREA_CHAPINERO, { lat: 4.64, lng: -74.0 })).toBeFalse();
    expect(dentroDelArea(AREA_CHAPINERO, { lat: 4.64, lng: -74.1 })).toBeFalse();
  });

  it('pans only when the card would cover the chosen marker', () => {
    const area = { norte: 10, sur: 0, este: 10, oeste: 0 };
    expect(desplazamientoTarjeta(area, 8, 400, 120)).toBe(0);
    expect(desplazamientoTarjeta(area, 1, 400, 120)).toBe(112);
    expect(desplazamientoTarjeta(area, 1, 400, 0)).toBe(0);
    expect(desplazamientoTarjeta({ ...area, sur: 10 }, 1, 400, 120)).toBe(0);
  });
});
