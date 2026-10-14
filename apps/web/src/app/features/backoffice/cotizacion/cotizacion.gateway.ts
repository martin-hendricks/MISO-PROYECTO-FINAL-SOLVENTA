import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export type TipoDispositivo = 'telefono' | 'tablet' | 'portatil';

export interface SolicitudCotizacion {
  cliente: { nombre: string; documento: string };
  ramo: 'dispositivo';
  vigenciaMeses: number;
  datosRiesgo: {
    tipo: TipoDispositivo;
    valorAsegurado: number;
    marca: string;
    modelo: string;
  };
}

/** Firm offer as the core prices it: amounts and currency code, never formatted. */
export interface Oferta {
  cotizacionId: string;
  estado: string;
  prima: number;
  primaNeta: number;
  gastosExpedicion: number;
  moneda: string;
  vigenciaMeses: number;
  venceEn: string;
}

@Injectable({ providedIn: 'root' })
export class CotizacionGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  quote(solicitud: SolicitudCotizacion): Observable<Oferta> {
    return this.http.post<Oferta>(`${this.baseUrl}/asesor/cotizaciones`, solicitud);
  }

  find(cotizacionId: string): Observable<Oferta> {
    return this.http.get<Oferta>(
      `${this.baseUrl}/asesor/cotizaciones/${encodeURIComponent(cotizacionId)}`,
    );
  }
}
