import { Role } from './session.service';

/** Unsigned token with the claims `bff-web` issues. For specs only. */
export function fakeAccessToken(rol: Role = 'cliente', expiresInSeconds = 900): string {
  const claims = {
    sub: 'camila@correo.com',
    rol,
    typ: 'access',
    exp: Math.floor(Date.now() / 1000) + expiresInSeconds,
  };
  return `header.${btoa(JSON.stringify(claims))}.signature`;
}

export function fakeTokenPair(rol: Role = 'cliente', expiresInSeconds = 900) {
  return {
    accessToken: fakeAccessToken(rol, expiresInSeconds),
    refreshToken: 'refresh',
    expiraEn: 900,
  };
}
