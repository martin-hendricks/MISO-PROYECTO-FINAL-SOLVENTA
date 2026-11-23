import { HttpBackend, HttpClient } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import {
  catchError,
  finalize,
  map,
  Observable,
  shareReplay,
  Subscription,
  tap,
  throwError,
  timer,
} from 'rxjs';
import { API_BASE_URL } from '../api/api-base-url';

export type Role = 'cliente' | 'asesor' | 'operador';

export interface Credentials {
  email: string;
  password: string;
  /** Left out in the back-office: the BFF assigns the role of the account. */
  role?: Role;
}

export interface TokenPair {
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

/** Rotate while the refresh token is still valid. Both tokens expire together. */
const REFRESH_LEAD_MS = 60_000;

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
  /** Bypasses interceptors so a refresh cannot recurse into itself. */
  private readonly raw = new HttpClient(inject(HttpBackend));
  private readonly baseUrl = inject(API_BASE_URL);
  private readonly pair = signal<TokenPair | null>(restore());
  private readonly claims = computed(() => {
    const pair = this.pair();
    return pair ? readClaims(pair.accessToken) : null;
  });
  private refreshInFlight: Observable<void> | null = null;
  private refreshTimer: Subscription | null = null;
  private generation = 0;

  readonly accessToken = computed(() => this.pair()?.accessToken ?? null);
  readonly role = computed(() => this.claims()?.rol ?? null);
  readonly subject = computed(() => this.claims()?.sub ?? null);

  constructor() {
    if (this.isActive()) this.scheduleRefresh();
  }

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
    return this.http
      .post<TokenPair>(`${this.baseUrl}/sesion/ingreso`, body)
      .pipe(map((pair) => this.start(pair)));
  }

  /** Opens the session with a pair the BFF already issued, as the sign-up does. */
  start(pair: TokenPair): void {
    if (!readClaims(pair.accessToken)) {
      throw new Error('Token ilegible');
    }
    this.pair.set(pair);
    persist(pair);
    this.scheduleRefresh();
  }

  /**
   * Rotates the stored pair. Callers share one request. A rejected refresh
   * ends the local session and does not call /sesion/salida.
   */
  refresh(): Observable<void> {
    if (this.refreshInFlight) return this.refreshInFlight;
    const refreshToken = this.pair()?.refreshToken;
    if (!refreshToken) {
      this.clearLocal();
      return throwError(() => new Error('Sin sesión'));
    }
    const generation = this.generation;
    const shared = this.raw
      .post<TokenPair>(`${this.baseUrl}/sesion/refresh`, { refreshToken })
      .pipe(
        tap((pair) => {
          if (generation === this.generation) this.start(pair);
        }),
        map(() => undefined),
        catchError((error) => {
          if (generation === this.generation) this.clearLocal();
          return throwError(() => error);
        }),
        finalize(() => {
          this.refreshInFlight = null;
        }),
        shareReplay(1),
      );
    this.refreshInFlight = shared;
    return shared;
  }

  signOut(): void {
    const token = this.accessToken();
    const refreshToken = this.pair()?.refreshToken;
    this.clearLocal();
    if (token) {
      // Best effort: the local session ends even if the BFF cannot be
      // reached. The refresh token travels in the body so the BFF can
      // revoke it too -- without this, a stolen refresh token keeps
      // working to mint new pairs after the user signs out (see
      // SessionService.refresh and bff-web/app/routers/sesion.py).
      this.http
        .post(`${this.baseUrl}/sesion/salida`, { refreshToken }, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .subscribe({ error: () => undefined });
    }
  }

  private scheduleRefresh(): void {
    this.refreshTimer?.unsubscribe();
    this.refreshTimer = null;
    const claims = this.claims();
    if (!claims || claims.exp * 1000 <= Date.now()) return;
    const delay = Math.max(0, claims.exp * 1000 - Date.now() - REFRESH_LEAD_MS);
    this.refreshTimer = timer(delay).subscribe(() => {
      this.refresh().subscribe({ error: () => undefined });
    });
  }

  private clearLocal(): void {
    this.generation += 1;
    this.refreshTimer?.unsubscribe();
    this.refreshTimer = null;
    this.pair.set(null);
    persist(null);
  }
}
