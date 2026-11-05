import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';

/** Shared customer profile from ms-identidad, projected by bff-web. */
export interface PerfilCliente {
  usuarioId: string;
  correo: string;
  nombre: string;
  apellidos: string;
  documento: string;
}

@Injectable({ providedIn: 'root' })
export class PerfilGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  load(): Observable<PerfilCliente> {
    return this.http.get<PerfilCliente>(`${this.baseUrl}/cliente/perfil`);
  }
}
