import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';
import { PolizaResumen } from '../polizas/polizas.gateway';

export interface Motivo {
  codigo: string;
  mensaje: string;
}

/** A core rejection is a business answer (200), not an HTTP error. */
export type ResultadoEmision =
  { resultado: 'EMITIDA'; poliza: PolizaResumen } | { resultado: 'RECHAZADA'; motivo: Motivo };

export interface Aceptacion {
  cotizacionId: string;
  ofertaId: string;
}

@Injectable({ providedIn: 'root' })
export class EmisionGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  accept(aceptacion: Aceptacion): Observable<ResultadoEmision> {
    return this.http.post<ResultadoEmision>(`${this.baseUrl}/cliente/polizas`, aceptacion);
  }
}
