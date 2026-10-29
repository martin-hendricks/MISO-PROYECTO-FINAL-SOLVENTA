import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export interface CotizacionPendiente {
  cotizacionId: string;
  ofertaId: string;
  ramo: string;
  estado: string;
  prima: number;
  moneda: string;
  creadaEn: string;
  venceEn: string;
  vencida: boolean;
  clienteRef: string | null;
}

export interface CotizacionesPagina {
  items: CotizacionPendiente[];
  pagina: number;
  tamano: number;
  hayMas: boolean;
  avisos: string[];
}

export interface CotizacionesFiltro {
  incluirVencidas: boolean;
  pagina: number;
}

export const TAMANO_PAGINA = 20;

@Injectable({ providedIn: 'root' })
export class CotizacionesGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** `GET /asesor/cotizaciones` (HU-163): the advisor's quotes pending issuance. */
  list(filtro: CotizacionesFiltro): Observable<CotizacionesPagina> {
    const params = new HttpParams()
      .set('incluirVencidas', filtro.incluirVencidas)
      .set('pagina', filtro.pagina)
      .set('tamano', TAMANO_PAGINA);
    return this.http.get<CotizacionesPagina>(`${this.baseUrl}/asesor/cotizaciones`, { params });
  }
}
