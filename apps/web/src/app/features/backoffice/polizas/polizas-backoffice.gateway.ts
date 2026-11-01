import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, Observable, of, throwError } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export interface Prima {
  valor: number;
  periodicidad: string;
}

/** Shape of GET/POST /operador/polizas/*, ver _poliza_salida() en bff-web. */
export interface PolizaOperador {
  numero: string;
  ramo: string;
  estado: 'vigente' | 'cancelada';
  venceEn: string;
  prima: Prima;
  /** Calculado server-side (Poliza.renovable en ms-polizas): la ventana de
   * gracia tras vencer es una regla de dominio, no se recalcula aquí. */
  renovable: boolean;
  devolucionEstimada: number | null;
  canceladaEn: string | null;
  canceladaPor: string | null;
  motivoCancelacion: string | null;
  siniestrosAbiertos: number | null;
}

interface PrimaWire {
  valor: number | string;
  periodicidad: string;
}

type PolizaOperadorWire = Omit<PolizaOperador, 'prima' | 'devolucionEstimada'> & {
  prima: PrimaWire;
  devolucionEstimada: number | string | null;
};

function toPoliza(wire: PolizaOperadorWire): PolizaOperador {
  return {
    ...wire,
    prima: { valor: Number(wire.prima.valor), periodicidad: wire.prima.periodicidad },
    devolucionEstimada: wire.devolucionEstimada === null ? null : Number(wire.devolucionEstimada),
  };
}

/** Typed core rejection (409/422), e.g. "ya cancelada" o "no renovable". */
export interface RechazoPoliza {
  codigo: string;
  mensaje: string;
}

export function rechazoDePoliza(error: unknown): RechazoPoliza | null {
  if (error instanceof HttpErrorResponse && (error.status === 409 || error.status === 422)) {
    const body = error.error as Partial<RechazoPoliza> | null;
    return { codigo: body?.codigo ?? 'rechazo', mensaje: body?.mensaje ?? '' };
  }
  return null;
}

@Injectable({ providedIn: 'root' })
export class PolizasBackofficeGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** `null` cuando no existe una póliza con ese número (404). */
  buscarPorNumero(numero: string): Observable<PolizaOperador | null> {
    return this.http
      .get<PolizaOperadorWire>(`${this.baseUrl}/operador/polizas/${encodeURIComponent(numero)}`)
      .pipe(
        map(toPoliza),
        catchError((error: unknown) =>
          error instanceof HttpErrorResponse && error.status === 404
            ? of(null)
            : throwError(() => error),
        ),
      );
  }

  renovar(numero: string): Observable<PolizaOperador> {
    return this.http
      .post<PolizaOperadorWire>(`${this.baseUrl}/operador/polizas/ciclo`, { numero, verbo: 'renovar' })
      .pipe(map(toPoliza));
  }

  cancelar(numero: string, motivo: string): Observable<PolizaOperador> {
    return this.http
      .post<PolizaOperadorWire>(`${this.baseUrl}/operador/polizas/ciclo`, {
        numero,
        verbo: 'cancelar',
        motivo,
      })
      .pipe(map(toPoliza));
  }
}
