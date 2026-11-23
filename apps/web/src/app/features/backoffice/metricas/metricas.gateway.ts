import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export type ConteoTipo =
  | 'PolizaEmitida'
  | 'PolizaRenovada'
  | 'PolizaModificada'
  | 'PolizaCancelada'
  | 'PolizaPorVencer';

export interface Conteo {
  tipo: ConteoTipo;
  fecha: string;
  cantidad: number;
}

interface MetricasWire {
  conteos: Conteo[];
}

@Injectable({ providedIn: 'root' })
export class MetricasGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** HU-68/69: conteos agregados de eventos de ciclo de vida de póliza --
   * el servicio analitica ya devuelve camelCase (tipo/fecha/cantidad), sin
   * necesidad de traducción wire. */
  conteos(desde: string, hasta: string): Observable<Conteo[]> {
    return this.http
      .get<MetricasWire>(`${this.baseUrl}/operador/metricas`, { params: { desde, hasta } })
      .pipe(map((wire) => wire.conteos));
  }
}
