import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';
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

@Injectable({ providedIn: 'root' })
export class PolizasGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  list(): Observable<PolizaResumen[]> {
    return this.http
      .get<{ polizas: PolizaResumen[] }>(`${this.baseUrl}/cliente/polizas`)
      .pipe(map((body) => body.polizas));
  }
}
