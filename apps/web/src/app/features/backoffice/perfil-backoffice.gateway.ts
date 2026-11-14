import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';

/** Perfil del asesor/operador logueado, proyectado por bff-web desde ms-identidad. */
export interface PerfilBackoffice {
  usuarioId: string;
  correo: string;
  nombre: string;
  apellidos: string;
  rol: string;
}

@Injectable({ providedIn: 'root' })
export class PerfilBackofficeGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  load(): Observable<PerfilBackoffice> {
    return this.http.get<PerfilBackoffice>(`${this.baseUrl}/backoffice/perfil`);
  }
}
