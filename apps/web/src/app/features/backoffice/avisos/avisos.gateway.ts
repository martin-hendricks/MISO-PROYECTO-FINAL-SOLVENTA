import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export type FiltroCola = 'pendientes' | 'aprobados' | 'rechazados' | 'todos';
export const FILTROS: readonly FiltroCola[] = ['pendientes', 'aprobados', 'rechazados', 'todos'];

/** Etiqueta del badge que calcula bff-web (_estado_cola en routers/siniestros.py). */
export type EstadoCola =
  'en_revision' | 'aprobado' | 'rechazado' | 'enrutado' | 'pagado' | 'recibido' | 'en_evaluacion';

export interface AvisoFila {
  id: string;
  siniestroId: string;
  clienteId: string | null;
  poliza: string;
  ramo: string;
  recibidoEn: string;
  estado: string;
  estadoCola: EstadoCola;
  resultado: 'aprobado' | 'rechazado' | null;
  requiereRevision: boolean;
}

export interface Cola {
  filtro: FiltroCola;
  conteos: Record<FiltroCola, number>;
  avisos: AvisoFila[];
}

export interface ReglaEvaluada {
  codigo: string;
  cumple: boolean;
  detalle: string;
}

export interface DecisionAuditada {
  origen: 'motor' | 'operador';
  actor: string;
  resultado: string;
  motivo: string | null;
  reglas: ReglaEvaluada[];
  decidida_en: string;
}

export interface PagoAviso {
  clave_idempotencia: string;
  comprobante: string;
  monto: string;
  origen: string;
  autorizado_por: string;
  pagado_en: string;
}

export interface IntentoPago {
  resultado: 'ejecutado' | 'reintento_idempotente';
  comprobante_devuelto: string;
  actor: string;
  ocurrido_en: string;
}

export interface CasoAviso extends AvisoFila {
  fechaHecho: string | null;
  descripcion: string | null;
  geo: { lat: string; lng: string; precision_m: string | null } | null;
  montoEstimado: number | null;
  umbralAutomatico: number | null;
  bajoMonto: boolean;
  moneda: string;
  clavePago: string;
  motivoRevision: string | null;
  evidencia: { nombre: string; tipo: string; contentType: string; url: string }[];
  decisiones: DecisionAuditada[];
  historial: { estado: string; fecha: string }[];
  pago: PagoAviso | null;
  intentosPago: IntentoPago[];
}

export interface ResultadoPago {
  pago: PagoAviso;
  reintento: boolean;
  caso: CasoAviso;
}

/** Rechazo tipificado del núcleo (409 transición inválida, 422 regla de negocio). */
export function rechazoDelNucleo(error: unknown): string | null {
  if (error instanceof HttpErrorResponse && (error.status === 409 || error.status === 422)) {
    return (error.error as { mensaje?: string } | null)?.mensaje ?? '';
  }
  return null;
}

@Injectable({ providedIn: 'root' })
export class AvisosGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  cola(filtro: FiltroCola): Observable<Cola> {
    return this.http.get<Cola>(`${this.baseUrl}/operador/avisos`, {
      params: new HttpParams().set('filtro', filtro),
    });
  }

  caso(id: string): Observable<CasoAviso> {
    return this.http.get<CasoAviso>(`${this.baseUrl}/operador/avisos/${encodeURIComponent(id)}`);
  }

  decidir(
    id: string,
    decision: 'aprobar' | 'rechazar',
    motivo: string | null,
  ): Observable<CasoAviso> {
    return this.http.post<CasoAviso>(`${this.baseUrl}/operador/avisos/decision`, {
      siniestroId: id,
      decision,
      motivo,
    });
  }

  enrutarAPerito(id: string, motivo: string | null): Observable<CasoAviso> {
    return this.http.post<CasoAviso>(
      `${this.baseUrl}/operador/avisos/${encodeURIComponent(id)}/perito`,
      { motivo },
    );
  }

  pagar(id: string): Observable<ResultadoPago> {
    return this.http.post<ResultadoPago>(
      `${this.baseUrl}/operador/avisos/${encodeURIComponent(id)}/pago`,
      {},
    );
  }
}
