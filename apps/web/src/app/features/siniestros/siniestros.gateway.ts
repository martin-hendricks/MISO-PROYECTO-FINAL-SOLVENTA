import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';

export interface SiniestroResumen {
  siniestroId: string;
  estado: string;
}

export interface PagoParametrico {
  siniestroId: string;
  poliza: string;
  umbral: string;
  monto: number;
  moneda: string;
  estado: string;
}

@Injectable({ providedIn: 'root' })
export class SiniestrosGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** Home already carries the open claim. This reads the same customer record. */
  load(): Observable<{ siniestroEnCurso: SiniestroResumen | null }> {
    return this.http.get<{ siniestroEnCurso: SiniestroResumen | null }>(
      `${this.baseUrl}/cliente/inicio`,
    );
  }

  /** Stored parametric payout. The summary is a claim outcome, not a premium charge. */
  parametric(): Observable<PagoParametrico> {
    return this.http.get<PagoParametrico>(`${this.baseUrl}/cliente/pagos-automaticos`);
  }
}
