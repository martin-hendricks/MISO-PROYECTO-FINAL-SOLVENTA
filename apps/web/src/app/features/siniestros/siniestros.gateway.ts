import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, Observable, of, throwError } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';

/** Estado único del núcleo (HU-30). El cliente solo lo observa: no aprueba ni paga. */
export type EstadoSiniestro = 'recibido' | 'en_evaluacion' | 'decidido' | 'enrutado' | 'pagado';
export type ResultadoSiniestro = 'aprobado' | 'rechazado' | null;

/** Fila de Mis siniestros (GET /cliente/siniestros, routers/siniestros.py de bff-web). */
export interface SiniestroResumen {
  id: string;
  siniestroId: string;
  tipo: 'asistido' | 'parametrico';
  ramo: string;
  poliza: string | null;
  resumen: string;
  fecha: string | null;
  estado: EstadoSiniestro;
  resultado: ResultadoSiniestro;
  reserva: number | null;
  moneda: string;
}

export interface Evidencia {
  nombre: string;
  tipo: string;
  contentType: string;
  /** URL firmada y temporal: la evidencia es privada. */
  url: string;
}

export interface SiniestroDetalle extends SiniestroResumen {
  descripcion: string | null;
  geo: { lat: string; lng: string; precision_m: string | null } | null;
  motivo: string | null;
  historial: { estado: EstadoSiniestro; fecha: string }[];
  evidencia: Evidencia[];
  pago: { comprobante: string; monto: number; moneda: string; fecha: string } | null;
}

export interface Ubicacion {
  lat: number;
  lng: number;
  precisionM: number | null;
}

export interface NuevoAviso {
  poliza: string;
  fechaHecho: string;
  descripcion: string;
  archivo: File;
  ubicacion: Ubicacion | null;
}

/** POST /cliente/siniestros: el núcleo responde `recibido` y evalúa después. */
export interface AvisoRecibido {
  id: string;
  siniestroId: string;
  estado: EstadoSiniestro;
}

/** Rechazo tipificado del núcleo (p. ej. evidencia_tipo_no_permitido). */
export interface RechazoAviso {
  codigo: string;
  mensaje: string;
}

export function esRechazoAviso(error: unknown): RechazoAviso | null {
  if (error instanceof HttpErrorResponse && (error.status === 422 || error.status === 409)) {
    const cuerpo = error.error as Partial<RechazoAviso> | null;
    return { codigo: cuerpo?.codigo ?? 'rechazado', mensaje: cuerpo?.mensaje ?? '' };
  }
  return null;
}

/** Tarjeta de Inicio: el siniestro abierto más reciente (GET /cliente/inicio). */
export interface SiniestroEnCurso {
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

interface SiniestroWire extends Omit<SiniestroResumen, 'reserva'> {
  reserva: number | string | null;
}

function toResumen<T extends SiniestroWire>(wire: T): T & { reserva: number | null } {
  return { ...wire, reserva: wire.reserva === null ? null : Number(wire.reserva) };
}

@Injectable({ providedIn: 'root' })
export class SiniestrosGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** Home already carries the open claim. This reads the same customer record. */
  load(): Observable<{ siniestroEnCurso: SiniestroEnCurso | null }> {
    return this.http.get<{ siniestroEnCurso: SiniestroEnCurso | null }>(
      `${this.baseUrl}/cliente/inicio`,
    );
  }

  /** Stored parametric payout. The summary is a claim outcome, not a premium charge. */
  parametric(): Observable<PagoParametrico> {
    return this.http.get<PagoParametrico>(`${this.baseUrl}/cliente/pagos-automaticos`);
  }

  list(): Observable<SiniestroResumen[]> {
    return this.http
      .get<{ siniestros: SiniestroWire[] }>(`${this.baseUrl}/cliente/siniestros`)
      .pipe(map((body) => body.siniestros.map(toResumen)));
  }

  /** `null` cuando no existe o es de otro cliente (ambos son 404). */
  detail(id: string): Observable<SiniestroDetalle | null> {
    return this.http
      .get<SiniestroDetalle>(`${this.baseUrl}/cliente/siniestros/${encodeURIComponent(id)}`)
      .pipe(
        map(toResumen),
        catchError((error: unknown) =>
          error instanceof HttpErrorResponse && error.status === 404
            ? of(null)
            : throwError(() => error),
        ),
      );
  }

  /** La misma `claveIdempotencia` en un reintento devuelve el aviso original (sin duplicar). */
  report(aviso: NuevoAviso, claveIdempotencia: string): Observable<AvisoRecibido> {
    const form = new FormData();
    form.append('poliza', aviso.poliza);
    form.append('fechaHecho', aviso.fechaHecho);
    form.append('descripcion', aviso.descripcion);
    form.append('archivos', aviso.archivo, aviso.archivo.name);
    if (aviso.ubicacion) {
      form.append('geo', JSON.stringify(aviso.ubicacion));
    }
    return this.http.post<AvisoRecibido>(`${this.baseUrl}/cliente/siniestros`, form, {
      headers: new HttpHeaders({ 'Idempotency-Key': claveIdempotencia }),
    });
  }
}
