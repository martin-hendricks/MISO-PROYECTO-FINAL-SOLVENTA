import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, Observable, of, throwError } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';

export type EstadoPoliza = 'VIGENTE' | 'CANCELADA';

export interface PolizaResumen {
  numero: string;
  producto: string;
  estado: EstadoPoliza;
  inicioVigencia: string;
  finVigencia: string;
  moneda: string;
  primaTotal: number;
}

export interface Cobertura {
  nombre: string;
  sumaAsegurada: number;
  deducible: number;
}

export interface PolizaDetalle extends PolizaResumen {
  coberturas: Cobertura[];
}

@Injectable({ providedIn: 'root' })
export class PolizasGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  list(): Observable<PolizaResumen[]> {
    return this.http
      .get<{ polizas: PolizaResumen[] }>(`${this.baseUrl}/cliente/polizas`)
      .pipe(map((body) => body.polizas));
  }

  /** `null` when the policy does not exist or belongs to another customer (both are 404). */
  detail(numero: string): Observable<PolizaDetalle | null> {
    return this.http
      .get<PolizaDetalle>(`${this.baseUrl}/cliente/polizas/${encodeURIComponent(numero)}`)
      .pipe(
        catchError((error: unknown) =>
          error instanceof HttpErrorResponse && error.status === 404
            ? of(null)
            : throwError(() => error),
        ),
      );
  }
}
