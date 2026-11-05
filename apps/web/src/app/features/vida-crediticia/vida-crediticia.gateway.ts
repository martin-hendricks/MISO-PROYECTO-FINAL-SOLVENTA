import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';
import { FactorOferta, Oferta, OfertaWire, toOferta } from '../cotizacion/cotizacion.gateway';

/** Mortgage the life cover is tied to: amount and term in months. */
export interface Credito {
  valor: number;
  plazoMeses: number;
}

/**
 * Mortgage life offer (HU-162): a firm `vida-crediticia` quote priced with the
 * profile Solventa built, so "Aceptar" emits it like any other offer (HU-114).
 */
export interface OfertaHipotecaria extends Oferta {
  factores: FactorOferta[];
  degradada: boolean;
  credito: Credito;
}

type OfertaHipotecariaWire = OfertaWire &
  Pick<OfertaHipotecaria, 'factores' | 'degradada' | 'credito'>;

/** Only the amounts need converting; factors, degradation and mortgage pass through. */
const toOfertaHipotecaria = (wire: OfertaHipotecariaWire) => toOferta(wire) as OfertaHipotecaria;

@Injectable({ providedIn: 'root' })
export class VidaCrediticiaGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** Only called once the customer authorized profiling: consent is never implicit (HU-53). */
  offer(credito: Credito): Observable<OfertaHipotecaria> {
    return this.http
      .post<OfertaHipotecariaWire>(`${this.baseUrl}/cliente/oferta-hipotecaria`, {
        credito,
        consentimientoPerfil: true,
      })
      .pipe(map(toOfertaHipotecaria));
  }

  /** Assisted sale (HU-58): the customer authorized profiling in front of the advisor. */
  offerFor(clienteId: string, credito: Credito): Observable<OfertaHipotecaria> {
    return this.http
      .post<OfertaHipotecariaWire>(`${this.baseUrl}/asesor/oferta-hipotecaria`, {
        clienteId,
        credito,
        consentimientoPerfil: true,
      })
      .pipe(map(toOfertaHipotecaria));
  }
}
