import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, Observable, of, throwError } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';
import { TipoPrestador } from './tipo-prestador';

export class ServicioNoDisponible extends Error {
  readonly codigo = 'servicio_no_disponible' as const;
}

export interface Prestador {
  id: string;
  nombre: string;
  tipo: TipoPrestador;
  ramos: string[];
  direccion: string;
  ciudad: string;
  barrio: string;
  lat: number;
  lng: number;
  telefono: string;
  horario: string;
  distanciaKm: number | null;
}

export interface CentroPrestadores {
  lat: number;
  lng: number;
  origen: 'posicion' | 'ciudad' | 'siniestro';
}

export interface BusquedaPrestadores {
  centro: CentroPrestadores | null;
  radioKm: number;
  prestadores: Prestador[];
}

export interface SiniestroPrestadores {
  id: string;
  numero: string;
  ramo: string | null;
}

export interface BusquedaSiniestro extends BusquedaPrestadores {
  siniestro: SiniestroPrestadores;
  ramoFijo: string | null;
  sinGeoetiqueta: boolean;
}

export interface ConsultaPrestadores {
  lat?: number;
  lng?: number;
  ciudad?: string;
  ramo?: string | null;
  radioKm?: number;
}

interface PrestadorWire {
  id: string;
  nombre: string;
  tipo: TipoPrestador;
  ramos?: string[];
  direccion: string;
  ciudad: string;
  barrio: string;
  lat: number | string;
  lng: number | string;
  telefono: string;
  horario: string;
  distanciaKm?: number | string | null;
}

interface BusquedaWire {
  centro?: CentroPrestadores | null;
  radioKm?: number;
  prestadores?: PrestadorWire[];
}

interface BusquedaSiniestroWire extends BusquedaWire {
  siniestro: SiniestroPrestadores;
  ramoFijo: string | null;
  sinGeoetiqueta: boolean;
}

function distanciaDe(valor: number | string | null | undefined): number | null {
  return valor == null || valor === '' ? null : Number(valor);
}

export function mapPrestador(wire: PrestadorWire): Prestador {
  return {
    id: wire.id,
    nombre: wire.nombre,
    tipo: wire.tipo,
    ramos: wire.ramos ?? [],
    direccion: wire.direccion,
    ciudad: wire.ciudad,
    barrio: wire.barrio,
    lat: Number(wire.lat),
    lng: Number(wire.lng),
    telefono: wire.telefono,
    horario: wire.horario,
    distanciaKm: distanciaDe(wire.distanciaKm),
  };
}

function mapBusqueda(wire: BusquedaWire): BusquedaPrestadores {
  return {
    centro: wire.centro ?? null,
    radioKm: wire.radioKm ?? 10,
    prestadores: (wire.prestadores ?? []).map(mapPrestador),
  };
}

export function servicioCaido(error: unknown): Observable<never> {
  if (error instanceof HttpErrorResponse) {
    const detail = (error.error as { detail?: string } | null)?.detail;
    if (detail === 'servicio_no_disponible') {
      return throwError(() => new ServicioNoDisponible());
    }
  }
  return throwError(() => error);
}

@Injectable({ providedIn: 'root' })
export class PrestadoresGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** Near me (`lat`/`lng`) or a city. `ramo` is omitted for Todos. */
  buscar(consulta: ConsultaPrestadores): Observable<BusquedaPrestadores> {
    let params = new HttpParams();
    if (consulta.lat !== undefined && consulta.lng !== undefined) {
      params = params
        .set('lat', String(consulta.lat))
        .set('lng', String(consulta.lng))
        .set('radioKm', String(consulta.radioKm ?? 10));
    } else if (consulta.ciudad) {
      params = params.set('ciudad', consulta.ciudad);
    }
    if (consulta.ramo) {
      params = params.set('ramo', consulta.ramo);
    }
    return this.http
      .get<BusquedaWire>(`${this.baseUrl}/cliente/prestadores`, { params })
      .pipe(map(mapBusqueda), catchError(servicioCaido));
  }

  /** `null` when the claim does not exist or belongs to another customer. */
  porSiniestro(id: string, radioKm = 10): Observable<BusquedaSiniestro | null> {
    const params = new HttpParams().set('radioKm', String(radioKm));
    return this.http
      .get<BusquedaSiniestroWire>(
        `${this.baseUrl}/cliente/siniestros/${encodeURIComponent(id)}/prestadores`,
        { params },
      )
      .pipe(
        map((wire) => ({
          ...mapBusqueda(wire),
          siniestro: wire.siniestro,
          ramoFijo: wire.ramoFijo,
          sinGeoetiqueta: wire.sinGeoetiqueta,
        })),
        catchError((error: unknown) =>
          error instanceof HttpErrorResponse && error.status === 404
            ? of(null)
            : servicioCaido(error),
        ),
      );
  }
}
