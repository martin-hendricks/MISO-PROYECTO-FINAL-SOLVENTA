import { HttpClient } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { map, Observable } from 'rxjs';
import { API_BASE_URL } from '../api/api-base-url';

export type Role = 'cliente' | 'asesor' | 'operador';

export interface Credentials {
  email: string;
  password: string;
  /** Left out in the back-office: the BFF assigns the role of the account. */
  role?: Role;
}

interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiraEn: number;
}

interface Claims {
  sub: string;
  rol: Role;
  exp: number;
}

export const SESSION_STORAGE_KEY = 'solventa.session';

function readClaims(token: string): Claims | null {
  try {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const claims = JSON.parse(atob(payload));
    return typeof claims.rol === 'string' && typeof claims.exp === 'number' ? claims : null;
  } catch {
    return null;
  }
}

function restore(): TokenPair | null {
  try {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function persist(pair: TokenPair | null): void {
  try {
    if (pair) {
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(pair));
    } else {
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
  } catch {
    // Storage can be blocked; the session then lives only in memory.
  }
}

@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);
  private readonly pair = signal<TokenPair | null>(restore());
  private readonly claims = computed(() => {
    const pair = this.pair();
    return pair ? readClaims(pair.accessToken) : null;
  });

  readonly accessToken = computed(() => this.pair()?.accessToken ?? null);
  readonly role = computed(() => this.claims()?.rol ?? null);
  readonly subject = computed(() => this.claims()?.sub ?? null);

  isActive(): boolean {
    const claims = this.claims();
    return claims !== null && claims.exp * 1000 > Date.now();
  }

  hasRole(roles: readonly Role[]): boolean {
    const role = this.role();
    return this.isActive() && role !== null && roles.includes(role);
  }

  signIn(credentials: Credentials): Observable<void> {
    const body = {
      correo: credentials.email,
      contrasena: credentials.password,
      ...(credentials.role ? { rol: credentials.role } : {}),
    };
    return this.http.post<TokenPair>(`${this.baseUrl}/sesion/ingreso`, body).pipe(
      map((pair) => {
        if (!readClaims(pair.accessToken)) {
          throw new Error('Token ilegible');
        }
        this.pair.set(pair);
        persist(pair);
      }),
    );
  }

  signOut(): void {
    const token = this.accessToken();
    if (token) {
      // Best effort: the local session ends even if the BFF cannot be reached.
      this.http
        .post(`${this.baseUrl}/sesion/salida`, null, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .subscribe({ error: () => undefined });
    }
    this.pair.set(null);
    persist(null);
  }
}
