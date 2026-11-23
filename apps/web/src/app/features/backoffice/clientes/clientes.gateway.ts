import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export type EstadoCliente = 'ACTIVO' | 'INACTIVO';
export type FiltroEstado = '' | EstadoCliente;

export interface Cliente {
  usuarioId: string;
  nombre: string;
  apellidos: string;
  email: string;
  documento: string;
  estado: EstadoCliente;
  dispositivosActivos: number | null;
}

export interface PaginaClientes {
  clientes: Cliente[];
  pagina: number;
  hayMas: boolean;
}

export interface ClienteNuevo {
  tipoDocumento: string;
  documento: string;
  email: string;
  password: string;
  nombre: string;
  apellidos: string;
}

export interface ClienteEdicion {
  nombre: string;
  apellidos: string;
  email: string;
}

export interface ConsultaClientes {
  q: string;
  estado: FiltroEstado;
  pagina: number;
}

@Injectable({ providedIn: 'root' })
export class ClientesGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  list(consulta: ConsultaClientes): Observable<PaginaClientes> {
    let params = new HttpParams().set('pagina', String(consulta.pagina));
    const q = consulta.q.trim();
    if (q.length >= 2) {
      params = params.set('q', q);
    }
    if (consulta.estado) {
      params = params.set('estado', consulta.estado);
    }
    return this.http.get<PaginaClientes>(`${this.baseUrl}/operador/clientes`, { params });
  }

  create(body: ClienteNuevo): Observable<Cliente> {
    return this.http.post<Cliente>(`${this.baseUrl}/operador/clientes`, body);
  }

  update(usuarioId: string, body: ClienteEdicion): Observable<Cliente> {
    return this.http.patch<Cliente>(
      `${this.baseUrl}/operador/clientes/${encodeURIComponent(usuarioId)}`,
      body,
    );
  }

  setEstado(usuarioId: string, estado: EstadoCliente): Observable<Cliente> {
    return this.http.post<Cliente>(
      `${this.baseUrl}/operador/clientes/${encodeURIComponent(usuarioId)}/estado`,
      { estado },
    );
  }
}
