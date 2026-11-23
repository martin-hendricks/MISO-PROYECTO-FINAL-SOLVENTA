import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

/** Shape of GET /operador/reportes/*, ver ReporteSalida en ms-polizas (reenviado
 * tal cual por bff-web). `contenido` es el archivo completo como texto plano
 * (CSV del adaptador stub) -- no base64, no streaming. */
export interface ReporteGenerado {
  nombreArchivo: string;
  tipoContenido: string;
  contenido: string;
}

interface ReporteGeneradoWire {
  nombre_archivo: string;
  tipo_contenido: string;
  contenido: string;
}

function toReporte(wire: ReporteGeneradoWire): ReporteGenerado {
  return {
    nombreArchivo: wire.nombre_archivo,
    tipoContenido: wire.tipo_contenido,
    contenido: wire.contenido,
  };
}

@Injectable({ providedIn: 'root' })
export class ReportesGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** HU-62: extracto interno de pólizas/siniestros para el regulador -- nunca
   * el formato SFC real, lo define el adaptador stub de ms-polizas. */
  regulador(desde: string, hasta: string): Observable<ReporteGenerado> {
    return this.http
      .get<ReporteGeneradoWire>(`${this.baseUrl}/operador/reportes/regulador`, {
        params: { desde, hasta },
      })
      .pipe(map(toReporte));
  }

  /** HU-63: extracto de cartera/siniestralidad para la reaseguradora -- nunca
   * acoplado a ACORD, mismo adaptador stub. */
  reaseguradora(desde: string, hasta: string): Observable<ReporteGenerado> {
    return this.http
      .get<ReporteGeneradoWire>(`${this.baseUrl}/operador/reportes/reaseguradora`, {
        params: { desde, hasta },
      })
      .pipe(map(toReporte));
  }
}
