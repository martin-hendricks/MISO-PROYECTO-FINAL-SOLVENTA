import { cardDigits, cardReady, expiryMonth, expiryYear, groupCard } from './card-confirmation';

describe('card confirmation', () => {
  it('groups and stops at the franchise length', () => {
    expect(groupCard('41111111111111119999')).toBe('4111 1111 1111 1111');
    expect(groupCard('55000000000000041234')).toBe('5500 0000 0000 0004');
    expect(groupCard('378282246310005999')).toBe('3782 822463 10005');
    expect(groupCard('3056930902590499')).toBe('3056 930902 5904');
    expect(groupCard('36123456789012')).toBe('3612 345678 9012');
    expect(groupCard('38123456789012')).toBe('3812 345678 9012');
    expect(groupCard('2221000000000000')).toBe('2221 0000 0000 0000');
    expect(groupCard('341234567890123')).toBe('3412 345678 90123');
    expect(groupCard('2000000000000000')).toBe('2000 0000 0000 0000');
    expect(groupCard('2721000000000000')).toBe('2721 0000 0000 0000');
    expect(groupCard('2')).toBe('2');
  });

  it('regroups and drops extra digits when the prefix changes', () => {
    expect(groupCard('4111111111111111'.replace(/^4/, '37'))).toBe('3711 111111 11111');
  });

  it('pads month 2 through 9 and keeps year at two digits', () => {
    expect(expiryMonth('8')).toBe('08');
    expect(expiryMonth('1')).toBe('1');
    expect(expiryMonth('12')).toBe('12');
    expect(expiryMonth('13')).toBe('1');
    expect(expiryYear('2028')).toBe('20');
  });

  it('is ready only when every local field is complete', () => {
    expect(
      cardReady({
        holder: 'Camila Restrepo',
        digits: cardDigits('4111 1111 1111 1111'),
        month: '08',
        year: '28',
        code: '123',
      }),
    ).toBeTrue();
    expect(
      cardReady({ holder: '', digits: '4111111111111111', month: '08', year: '28', code: '123' }),
    ).toBeFalse();
  });
});
