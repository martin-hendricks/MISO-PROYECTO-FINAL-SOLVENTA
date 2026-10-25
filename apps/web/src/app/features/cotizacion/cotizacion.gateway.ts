import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, Observable, of, throwError } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';
import { DatosRiesgo, RAMO } from './soat-motocicleta';

/** Firm offer (HU-6): the core calculates it once and reconsulting returns the same price. */
export interface Oferta {
  cotizacionId: string;
  ramo: string;
  estado: string;
  prima: number;
  moneda: string;
  venceEn: string;
  /** Breakdown of the premium (HU-4); optional so an older answer still renders. */
  primaNeta?: number;
  expedicion?: number;
}

/** The core sends amounts as JSON decimals (strings); the channel formats numbers. */
type OfertaWire = Omit<Oferta, 'prima' | 'primaNeta' | 'expedicion'> & {
  prima: number | string;
  primaNeta?: number | string | null;
  expedicion?: number | string | null;
};

/** A risk datum of the line of business with its valid domain (HU-1). */
export type DatoRiesgo =
  | { nombre: string; tipo: 'rango'; minimo: number; maximo: number }
  | { nombre: string; tipo: 'valores'; valores: string[] };

export interface Catalogo {
  ramo: string;
  nombre: string;
  moneda: string;
  datosRiesgo: DatoRiesgo[];
}

type DatoRiesgoWire =
  | { nombre: string; tipo: 'rango'; minimo: number | string; maximo: number | string }
  | { nombre: string; tipo: 'valores'; valores: string[] };

type CatalogoWire = Omit<Catalogo, 'datosRiesgo'> & { datosRiesgo: DatoRiesgoWire[] };

function toCatalogo(wire: CatalogoWire): Catalogo {
  return {
    ramo: wire.ramo,
    nombre: wire.nombre,
    moneda: wire.moneda,
    datosRiesgo: wire.datosRiesgo.map((dato) =>
      dato.tipo === 'rango'
        ? { ...dato, minimo: Number(dato.minimo), maximo: Number(dato.maximo) }
        : dato,
    ),
  };
}

export type Canal = 'cliente' | 'asesor';

/** Typed core rejection of the risk data (HU-3), e.g. `dato_riesgo_fuera_de_rango`. */
export interface RechazoCotizacion {
  codigo: string;
  mensaje: string;
}

const optional = (amount: number | string | null | undefined) =>
  amount === null || amount === undefined ? undefined : Number(amount);

function toOferta(wire: OfertaWire): Oferta {
  return {
    ...wire,
    prima: Number(wire.prima),
    primaNeta: optional(wire.primaNeta),
    expedicion: optional(wire.expedicion),
  };
}

/** A 409/422 from the core is a business answer about the input, not an outage. */
export function rechazoDe(error: unknown): RechazoCotizacion | null {
  if (error instanceof HttpErrorResponse && (error.status === 409 || error.status === 422)) {
    const body = error.error as Partial<RechazoCotizacion> | null;
    return { codigo: body?.codigo ?? 'rechazo', mensaje: body?.mensaje ?? '' };
  }
  return null;
}

@Injectable({ providedIn: 'root' })
export class CotizacionGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** Valid ranges of the risk data, so the form blocks the CTA before quoting. */
  catalog(canal: Canal): Observable<Catalogo> {
    return this.http
      .get<CatalogoWire>(`${this.baseUrl}/${canal}/catalogo/${encodeURIComponent(RAMO)}`)
      .pipe(map(toCatalogo));
  }

  /** Customer quote of the single line of business. */
  quote(datosRiesgo: DatosRiesgo): Observable<Oferta> {
    return this.http
      .post<OfertaWire>(`${this.baseUrl}/cliente/cotizaciones`, { ramo: RAMO, datosRiesgo })
      .pipe(map(toOferta));
  }

  /** Assisted sale: the advisor quotes on behalf of the customer they serve. */
  quoteFor(clienteId: string, datosRiesgo: DatosRiesgo): Observable<Oferta> {
    return this.http
      .post<OfertaWire>(`${this.baseUrl}/asesor/cotizaciones`, {
        clienteId,
        ramo: RAMO,
        datosRiesgo,
      })
      .pipe(map(toOferta));
  }

  /** Reconsults by id without recalculating (HU-7); `null` when the quote does not exist. */
  find(cotizacionId: string): Observable<Oferta | null> {
    return this.http
      .get<OfertaWire>(`${this.baseUrl}/cliente/cotizaciones/${encodeURIComponent(cotizacionId)}`)
      .pipe(
        map(toOferta),
        catchError((error: unknown) =>
          error instanceof HttpErrorResponse && error.status === 404
            ? of(null)
            : throwError(() => error),
        ),
      );
  }
}
