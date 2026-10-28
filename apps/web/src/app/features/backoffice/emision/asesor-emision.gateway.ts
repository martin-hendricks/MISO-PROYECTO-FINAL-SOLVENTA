import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export interface Paso {
  paso: 'COTIZAR' | 'OFERTA' | 'EMISION' | 'POLIZA';
  estado: 'COMPLETADO' | 'ACTUAL' | 'ERROR' | 'PENDIENTE';
}

export interface Decision {
  resultado: 'ACEPTADA' | 'RECHAZADA';
  regla: string;
  detalle: string;
  decididoPor: string;
  decididoEn: string;
}

export interface ResumenOferta {
  moneda: string;
  primaTotal: number;
  primaNeta: number;
  expedicion: number;
  vigenciaMeses: number;
}

/** Accepted offer with the core subscription decision; nothing is issued yet. */
export interface SolicitudEmision {
  solicitudId: string;
  cliente: { clienteId: string; nombre: string };
  producto: string;
  referencia: string;
  pasos: Paso[];
  decision: Decision;
  oferta: ResumenOferta;
}

export interface EmisionAsesor {
  resultado: 'EMITIDA';
  pasos: Paso[];
  firma: { firmadaEn: string; hash: string };
  poliza: { numero: string; expedidaEn: string; inicioVigencia: string; finVigencia: string };
}

/** The core refused to issue (HU-17 failed signature): a business answer, not an HTTP error. */
export interface EmisionRechazada {
  resultado: 'RECHAZADA';
  motivo: string;
  pasos: Paso[];
}

export type ResultadoEmisionAsesor = EmisionAsesor | EmisionRechazada;

/** The offer is the quote (HU-6): bff-web creates the offer id on acceptance. */
export interface AceptacionAsesor {
  cotizacionId: string;
  clienteId: string;
}

@Injectable({ providedIn: 'root' })
export class AsesorEmisionGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  decide(aceptacion: AceptacionAsesor): Observable<SolicitudEmision> {
    return this.http.post<SolicitudEmision>(`${this.baseUrl}/asesor/emisiones`, aceptacion);
  }

  /** Signs (HU-17 stub) and issues an approved request. */
  issue(solicitudId: string): Observable<ResultadoEmisionAsesor> {
    return this.http.post<ResultadoEmisionAsesor>(
      `${this.baseUrl}/asesor/emisiones/${encodeURIComponent(solicitudId)}/poliza`,
      {},
    );
  }
}
