import { offerExpired } from './oferta-expiration';

describe('offerExpired', () => {
  const noon = new Date(2026, 5, 1, 12, 0, 0);

  it('keeps a future instant', () => {
    expect(offerExpired('2999-06-01T12:00:00Z', noon)).toBeFalse();
  });

  it('expires an instant that has already passed', () => {
    expect(offerExpired('2000-01-01T00:00:00Z', noon)).toBeTrue();
  });

  it('keeps a date-only value through that local day', () => {
    expect(offerExpired('2026-06-01', new Date(2026, 5, 1, 23, 0, 0))).toBeFalse();
  });

  it('expires a date-only value after that local day', () => {
    expect(offerExpired('2026-06-01', new Date(2026, 5, 2, 0, 0, 0))).toBeTrue();
  });

  it('fails closed when the value is missing or malformed', () => {
    expect(offerExpired(null, noon)).toBeTrue();
    expect(offerExpired(undefined, noon)).toBeTrue();
    expect(offerExpired('', noon)).toBeTrue();
    expect(offerExpired('no-es-fecha', noon)).toBeTrue();
  });
});
