import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';

/** A quote the customer can still accept. The BFF sends it only when it can be consulted again. */
export interface OfertaVigente {
  cotizacionId: string;
  ramo: string;
  estado: string;
}

export interface Poliza {
  numero: string;
  ramo: string;
  estado: string;
}

export interface SiniestroEnCurso {
  siniestroId: string;
  estado: string;
}

/** The Inicio aggregate of `bff-web` (contract HU-138). A `null` block draws no card. */
export interface Inicio {
  ofertaVigente: OfertaVigente | null;
  poliza: Poliza | null;
  siniestroEnCurso: SiniestroEnCurso | null;
  /** Present only when there is a mortgage origination. */
  hipotecario: { estado?: string } | null;
}

@Injectable({ providedIn: 'root' })
export class InicioGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  load(): Observable<Inicio> {
    return this.http.get<Inicio>(`${this.baseUrl}/cliente/inicio`);
  }
}
