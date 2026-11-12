import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';

export type ConsentimientoPerfil =
  | { estado: 'vigente'; otorgadoEn: string }
  | { estado: 'revocado'; revocadoEn: string }
  | { estado: 'sin_consentimiento' };

@Injectable({ providedIn: 'root' })
export class ConsentimientoPerfilGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  load(): Observable<ConsentimientoPerfil> {
    return this.http.get<ConsentimientoPerfil>(`${this.baseUrl}/cliente/consentimiento-perfil`);
  }

  revoke(): Observable<ConsentimientoPerfil> {
    return this.http.delete<ConsentimientoPerfil>(`${this.baseUrl}/cliente/consentimiento-perfil`);
  }
}
