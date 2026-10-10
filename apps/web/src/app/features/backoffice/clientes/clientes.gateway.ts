import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export interface Cliente {
  clienteId: string;
  nombre: string;
  documento: string;
  canal: 'web' | 'android';
  estado: 'activo' | 'inactivo';
  consentimiento: 'habeas_data' | 'hipotecario_pendiente' | 'revocado';
}

@Injectable({ providedIn: 'root' })
export class ClientesGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  list(): Observable<Cliente[]> {
    return this.http
      .get<{ clientes: Cliente[] }>(`${this.baseUrl}/asesor/clientes`)
      .pipe(map((body) => body.clientes));
  }
}
