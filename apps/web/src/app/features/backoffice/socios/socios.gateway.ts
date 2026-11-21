import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export type Alcance =
  'catalogo:leer' | 'originaciones:escribir' | 'cotizaciones:escribir' | 'cotizaciones:leer';

export const ALCANCES: readonly Alcance[] = [
  'catalogo:leer',
  'originaciones:escribir',
  'cotizaciones:escribir',
  'cotizaciones:leer',
];

export type EstadoSocio = 'activo' | 'revocado';

export interface CredencialSocio {
  credencialId: string;
  creadaEn: string;
  revocadaEn: string | null;
}

export interface Socio {
  socioId: string;
  nombre: string;
  alcances: Alcance[];
  estado: EstadoSocio;
  creadoEn: string;
  credenciales: CredencialSocio[];
}

export interface ListaSocios {
  socios: Socio[];
}

export interface SocioNuevo {
  nombre: string;
  alcances: Alcance[];
}

export interface SocioCreado {
  socioId: string;
  nombre: string;
  alcances: Alcance[];
  estado: EstadoSocio;
  creadoEn: string;
  credencialId: string;
  apiKey: string;
}

export interface CredencialEmitida {
  credencialId: string;
  apiKey: string;
}

@Injectable({ providedIn: 'root' })
export class SociosGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  private url(...partes: string[]): string {
    return [`${this.baseUrl}/backoffice/socios`, ...partes.map(encodeURIComponent)].join('/');
  }

  list(): Observable<ListaSocios> {
    return this.http.get<ListaSocios>(this.url());
  }

  create(body: SocioNuevo): Observable<SocioCreado> {
    return this.http.post<SocioCreado>(this.url(), body);
  }

  rotate(socioId: string): Observable<CredencialEmitida> {
    return this.http.post<CredencialEmitida>(this.url(socioId, 'credenciales'), {});
  }

  revokeCredential(socioId: string, credencialId: string): Observable<void> {
    return this.http.delete<void>(this.url(socioId, 'credenciales', credencialId));
  }

  revoke(socioId: string): Observable<Socio> {
    return this.http.post<Socio>(this.url(socioId, 'revocacion'), {});
  }
}
