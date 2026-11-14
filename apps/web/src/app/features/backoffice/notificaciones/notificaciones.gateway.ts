import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export interface UsuarioAudiencia {
  usuarioId: string;
  nombre: string;
  apellidos: string;
  email: string;
  documento: string;
  dispositivosActivos: number;
}

export interface AudienciaDifusion {
  tipo: 'todos' | 'usuarios';
  usuarioIds?: string[];
}

export interface DifusionEntrada {
  titulo: string;
  cuerpo: string;
  audiencia: AudienciaDifusion;
  poliza?: string;
}

export interface DifusionResultado {
  difusionId: string;
  enviadas: number;
  fallidas: number;
  sinDispositivo: number;
}

export interface DifusionItem extends DifusionResultado {
  titulo: string;
  cuerpo: string;
  poliza: string | null;
  creadaEn: string;
}

function texto(...valores: unknown[]): string {
  for (const valor of valores) {
    if (typeof valor === 'string' && valor.trim()) {
      return valor.trim();
    }
    if (typeof valor === 'number') {
      return String(valor);
    }
  }
  return '';
}

export function usuarioAudiencia(fila: Record<string, unknown>): UsuarioAudiencia {
  return {
    usuarioId: texto(fila['usuarioId'], fila['usuario_id']),
    nombre: texto(fila['nombre']),
    apellidos: texto(fila['apellidos']),
    email: texto(fila['email'], fila['correo']),
    documento: texto(fila['documento'], fila['numeroDocumento'], fila['numero_documento']),
    dispositivosActivos: Number(fila['dispositivosActivos'] ?? fila['dispositivos_activos'] ?? 0),
  };
}

@Injectable({ providedIn: 'root' })
export class NotificacionesGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  audiencia(): Observable<{ usuarios: UsuarioAudiencia[] }> {
    return this.http
      .get<{ usuarios?: Array<Record<string, unknown>> }>(
        `${this.baseUrl}/operador/notificaciones/audiencia`,
      )
      .pipe(map((body) => ({ usuarios: (body.usuarios ?? []).map(usuarioAudiencia) })));
  }

  enviar(body: DifusionEntrada): Observable<DifusionResultado> {
    return this.http.post<DifusionResultado>(
      `${this.baseUrl}/operador/notificaciones/difusiones`,
      body,
    );
  }

  historial(limite?: number, antesDe?: string): Observable<{ items: DifusionItem[] }> {
    let params = new HttpParams();
    if (limite !== undefined) {
      params = params.set('limite', String(limite));
    }
    if (antesDe) {
      params = params.set('antesDe', antesDe);
    }
    return this.http.get<{ items: DifusionItem[] }>(
      `${this.baseUrl}/operador/notificaciones/difusiones`,
      { params },
    );
  }
}
