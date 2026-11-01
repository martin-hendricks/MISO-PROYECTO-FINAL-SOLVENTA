import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';
import { TokenPair } from '../../core/session/session.service';
import { Alta } from '../registro/registro.draft';

/** What `bff-web` records when the customer grants habeas data (HA-21). */
export interface MarcaConsentimiento {
  habeasData: boolean;
  otorgadoEn: string;
  version: string;
}

/** The sign-up answer: the account, its consent mark and the session of the new customer. */
export interface Registro extends TokenPair {
  cliente: Omit<Alta, 'contrasena'>;
  consentimiento: MarcaConsentimiento;
}

@Injectable({ providedIn: 'root' })
export class ConsentimientoGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** Creates the account. The consent travels with the sign-up, never on its own. */
  grant(alta: Alta): Observable<Registro> {
    return this.http.post<Registro>(`${this.baseUrl}/registro`, { ...alta, habeasData: true });
  }
}
