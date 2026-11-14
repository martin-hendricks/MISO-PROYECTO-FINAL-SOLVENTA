import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, Observable, of, throwError } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';

export type TipoDeposito = 'asistido' | 'pago_automatico';

export interface Movimiento {
  id: string;
  siniestroId: string;
  tipo: TipoDeposito;
  ramo: string;
  resumen: string;
  poliza: string | null;
  monto: number;
  moneda: string;
  comprobante: string;
  depositadoEn: string;
}

export interface Billetera {
  moneda: string;
  totalRecibido: number;
  movimientos: Movimiento[];
}

@Injectable({ providedIn: 'root' })
export class BilleteraGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  list(): Observable<Billetera> {
    return this.http.get<Billetera>(`${this.baseUrl}/cliente/billetera`);
  }

  /** `null` cuando el depósito no existe o es de otro cliente (ambos son 404). */
  detail(id: string): Observable<Movimiento | null> {
    return this.http
      .get<Movimiento>(`${this.baseUrl}/cliente/billetera/${encodeURIComponent(id)}`)
      .pipe(
        catchError((error: unknown) =>
          error instanceof HttpErrorResponse && error.status === 404
            ? of(null)
            : throwError(() => error),
        ),
      );
  }
}
