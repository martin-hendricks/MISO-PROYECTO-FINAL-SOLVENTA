import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, Observable, of, throwError } from 'rxjs';
import { API_BASE_URL } from '../../core/api/api-base-url';
import { Pais, TipoPrestador } from './tipo-prestador';

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
  pais: Pais;
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
  radioKm: number | null;
  truncado: boolean;
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

/** Visible rectangle of the map, in degrees. */
export interface AreaVisible {
  norte: number;
  sur: number;
  este: number;
  oeste: number;
}

export interface CiudadMapa {
  nombre: string;
  lat: number;
  lng: number;
  zoom: number;
  prestadores: number;
}

/** With `area` the BFF ignores radius and city; `origen` only measures distance. */
export interface ConsultaPrestadores {
  area?: AreaVisible;
  origen?: { lat: number; lng: number };
  ciudad?: string;
  pais?: Pais;
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
  pais?: Pais;
  barrio: string;
  lat: number | string;
  lng: number | string;
  telefono: string;
  horario: string;
  distanciaKm?: number | string | null;
}

interface BusquedaWire {
  centro?: { lat: number | string; lng: number | string; origen: CentroPrestadores['origen'] } | null;
  radioKm?: number | null;
  truncado?: boolean;
  prestadores?: PrestadorWire[];
}

interface BusquedaSiniestroWire extends BusquedaWire {
  siniestro: SiniestroPrestadores;
  ramoFijo: string | null;
  sinGeoetiqueta: boolean;
}

interface CiudadWire {
  nombre: string;
  lat: number | string;
  lng: number | string;
  zoom: number | string;
  prestadores: number | string;
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
    pais: wire.pais ?? 'CO',
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
    centro: wire.centro
      ? { lat: Number(wire.centro.lat), lng: Number(wire.centro.lng), origen: wire.centro.origen }
      : null,
    radioKm: wire.radioKm ?? null,
    truncado: wire.truncado ?? false,
    prestadores: (wire.prestadores ?? []).map(mapPrestador),
  };
}

function mapCiudad(wire: CiudadWire): CiudadMapa {
  return {
    nombre: wire.nombre,
    lat: Number(wire.lat),
    lng: Number(wire.lng),
    zoom: Number(wire.zoom),
    prestadores: Number(wire.prestadores),
  };
}

function conArea(params: HttpParams, area: AreaVisible): HttpParams {
  return params
    .set('norte', String(area.norte))
    .set('sur', String(area.sur))
    .set('este', String(area.este))
    .set('oeste', String(area.oeste));
}

/** The BFF answers `{codigo, mensaje}`, not FastAPI's `detail`. */
export function servicioCaido(error: unknown): Observable<never> {
  if (error instanceof HttpErrorResponse) {
    const codigo = (error.error as { codigo?: string } | null)?.codigo;
    if (codigo === 'servicio_no_disponible') {
      return throwError(() => new ServicioNoDisponible());
    }
  }
  return throwError(() => error);
}

@Injectable({ providedIn: 'root' })
export class PrestadoresGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  /** Visible area, near me (`origen`) or a city. `ramo` is omitted for Todos. */
  buscar(consulta: ConsultaPrestadores): Observable<BusquedaPrestadores> {
    let params = new HttpParams();
    if (consulta.area) {
      params = conArea(params, consulta.area);
    }
    if (consulta.origen) {
      params = params.set('lat', String(consulta.origen.lat)).set('lng', String(consulta.origen.lng));
      if (!consulta.area) {
        params = params.set('radioKm', String(consulta.radioKm ?? 10));
      }
    } else if (consulta.ciudad) {
      params = params.set('ciudad', consulta.ciudad);
    }
    if (consulta.pais) {
      params = params.set('pais', consulta.pais);
    }
    if (consulta.ramo) {
      params = params.set('ramo', consulta.ramo);
    }
    return this.http
      .get<BusquedaWire>(`${this.baseUrl}/cliente/prestadores`, { params })
      .pipe(map(mapBusqueda), catchError(servicioCaido));
  }

  /** Cities of the country with at least one active provider, in catalog order. */
  ciudades(pais: Pais): Observable<CiudadMapa[]> {
    const params = new HttpParams().set('pais', pais);
    return this.http
      .get<{ ciudades?: CiudadWire[] }>(`${this.baseUrl}/cliente/prestadores/ciudades`, { params })
      .pipe(
        map((wire) => (wire.ciudades ?? []).map(mapCiudad)),
        catchError(servicioCaido),
      );
  }

  /** `null` when the claim does not exist or belongs to another customer. */
  porSiniestro(id: string, area?: AreaVisible): Observable<BusquedaSiniestro | null> {
    const params = area ? conArea(new HttpParams(), area) : new HttpParams().set('radioKm', '10');
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
