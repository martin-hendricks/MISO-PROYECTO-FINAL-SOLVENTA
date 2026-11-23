import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, Observable, of, throwError } from 'rxjs';
import { API_BASE_URL } from '../../../core/api/api-base-url';
import { CiudadMapa } from '../../prestadores/prestadores.gateway';
import { Pais, TipoPrestador } from '../../prestadores/tipo-prestador';

export type EstadoPrestador = 'activo' | 'inactivo';

export interface PrestadorOperador {
  id: string;
  nombre: string;
  tipo: TipoPrestador;
  ramos: string[];
  direccion: string;
  pais: Pais;
  ciudad: string;
  barrio: string;
  lat: number;
  lng: number;
  telefono: string;
  horario: string;
  estado: EstadoPrestador;
  actualizadoEn: string;
}

export interface PrestadorEntrada {
  nombre: string;
  tipo: TipoPrestador;
  ramos: string[];
  direccion: string;
  pais: Pais;
  ciudad: string;
  barrio: string;
  lat: number;
  lng: number;
  telefono: string;
  horario: string;
}

export interface FiltroOperador {
  pais?: Pais;
  ramo?: string;
  ciudad?: string;
  estado?: EstadoPrestador;
}

export interface ListadoOperador {
  pais: Pais;
  conteos: Record<string, number>;
  centro: { lat: number; lng: number } | null;
  prestadores: PrestadorOperador[];
}

interface FilaWire {
  id: string;
  nombre: string;
  tipo: TipoPrestador;
  ramos?: string[];
  direccion: string;
  pais?: Pais;
  ciudad: string;
  barrio: string;
  lat: number | string;
  lng: number | string;
  telefono: string;
  horario: string;
  estado: EstadoPrestador;
  actualizadoEn?: string;
}

function filaDe(wire: FilaWire): PrestadorOperador {
  return {
    id: wire.id,
    nombre: wire.nombre,
    tipo: wire.tipo,
    ramos: wire.ramos ?? [],
    direccion: wire.direccion,
    pais: wire.pais ?? 'CO',
    ciudad: wire.ciudad,
    barrio: wire.barrio,
    lat: Number(wire.lat),
    lng: Number(wire.lng),
    telefono: wire.telefono,
    horario: wire.horario,
    estado: wire.estado,
    actualizadoEn: wire.actualizadoEn ?? '',
  };
}

function conteosDe(valor: Record<string, number | string> | null | undefined): Record<string, number> {
  return Object.fromEntries(
    Object.entries(valor ?? {}).map(([ciudad, total]) => [ciudad, Number(total)]),
  );
}

interface CiudadWire {
  nombre: string;
  lat: number | string;
  lng: number | string;
  zoom: number;
  prestadores: number;
}

@Injectable({ providedIn: 'root' })
export class BoPrestadoresGateway {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  ciudades(pais: Pais): Observable<CiudadMapa[]> {
    return this.http
      .get<{ ciudades?: CiudadWire[] }>(`${this.baseUrl}/operador/prestadores/ciudades`, {
        params: new HttpParams().set('pais', pais),
      })
      .pipe(
        map((body) =>
          (body.ciudades ?? []).map((ciudad) => ({
            nombre: ciudad.nombre,
            lat: Number(ciudad.lat),
            lng: Number(ciudad.lng),
            zoom: ciudad.zoom,
            prestadores: ciudad.prestadores,
          })),
        ),
      );
  }

  listar(filtro: FiltroOperador = {}): Observable<ListadoOperador> {
    let params = new HttpParams();
    if (filtro.pais) {
      params = params.set('pais', filtro.pais);
    }
    if (filtro.ramo) {
      params = params.set('ramo', filtro.ramo);
    }
    if (filtro.ciudad) {
      params = params.set('ciudad', filtro.ciudad);
    }
    if (filtro.estado) {
      params = params.set('estado', filtro.estado);
    }
    return this.http
      .get<{
        pais?: Pais;
        conteos?: Record<string, number | string> | null;
        centro?: { lat: number | string; lng: number | string } | null;
        prestadores?: FilaWire[];
      }>(`${this.baseUrl}/operador/prestadores`, { params })
      .pipe(
        map((body) => ({
          pais: body.pais ?? filtro.pais ?? 'CO',
          conteos: conteosDe(body.conteos),
          centro: body.centro
            ? { lat: Number(body.centro.lat), lng: Number(body.centro.lng) }
            : null,
          prestadores: (body.prestadores ?? []).map(filaDe),
        })),
      );
  }

  obtener(id: string): Observable<PrestadorOperador | null> {
    return this.http
      .get<FilaWire>(`${this.baseUrl}/operador/prestadores/${encodeURIComponent(id)}`)
      .pipe(
        map(filaDe),
        catchError((error: unknown) =>
          error instanceof HttpErrorResponse && error.status === 404
            ? of(null)
            : throwError(() => error),
        ),
      );
  }

  crear(entrada: PrestadorEntrada): Observable<PrestadorOperador> {
    return this.http
      .post<FilaWire>(`${this.baseUrl}/operador/prestadores`, entrada)
      .pipe(map(filaDe));
  }

  editar(id: string, entrada: PrestadorEntrada): Observable<PrestadorOperador> {
    return this.http
      .patch<FilaWire>(`${this.baseUrl}/operador/prestadores/${encodeURIComponent(id)}`, entrada)
      .pipe(map(filaDe));
  }

  cambiarEstado(id: string, estado: EstadoPrestador): Observable<PrestadorOperador> {
    return this.http
      .post<FilaWire>(`${this.baseUrl}/operador/prestadores/${encodeURIComponent(id)}/estado`, {
        estado,
      })
      .pipe(map(filaDe));
  }
}
