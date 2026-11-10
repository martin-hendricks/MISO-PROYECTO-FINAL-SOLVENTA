import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';

export interface UsuarioAudiencia {
  usuarioId: string;
  nombre: string;
  apellidos: string;
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

@Injectable({ providedIn: 'root' })
export class NotificacionesGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  audiencia(): Observable<{ usuarios: UsuarioAudiencia[] }> {
    return this.http.get<{ usuarios: UsuarioAudiencia[] }>(
      `${this.baseUrl}/operador/notificaciones/audiencia`,
    );
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
