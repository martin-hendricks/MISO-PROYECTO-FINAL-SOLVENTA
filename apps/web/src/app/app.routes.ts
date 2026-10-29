import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { redirectSignedIn, requireRole } from './core/session/session.guard';
import { Role, SessionService } from './core/session/session.service';
import { homeSection, Section } from './features/backoffice/sections';
import type { Destino } from './features/destino/destino.view';
import { BACKOFFICE_LOGIN, CUSTOMER_LOGIN } from './features/login/login.variant';
import { requireDraft } from './features/registro/registro.draft';

const CUSTOMER: readonly Role[] = ['cliente'];
const STAFF: readonly Role[] = ['asesor', 'operador'];

const loadLogin = () => import('./features/login/login.view').then((m) => m.LoginView);
const loadSection = () =>
  import('./features/backoffice/section/section.view').then((m) => m.SectionView);
const section = (name: Section) => ({
  path: name,
  data: { section: name },
  loadComponent: loadSection,
});
const destino = (path: string, name: Destino) => ({
  path,
  data: { destino: name },
  loadComponent: () => import('./features/destino/destino.view').then((m) => m.DestinoView),
});

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [redirectSignedIn(CUSTOMER, CUSTOMER_LOGIN.home)],
    data: { login: CUSTOMER_LOGIN },
    loadComponent: loadLogin,
  },
  {
    path: 'registro',
    canActivate: [redirectSignedIn(CUSTOMER, CUSTOMER_LOGIN.home)],
    loadComponent: () => import('./features/registro/registro.view').then((m) => m.RegistroView),
  },
  {
    path: 'consentimiento',
    canActivate: [redirectSignedIn(CUSTOMER, CUSTOMER_LOGIN.home), requireDraft],
    loadComponent: () =>
      import('./features/consentimiento/consentimiento.view').then((m) => m.ConsentimientoView),
  },
  {
    path: 'cms/login',
    canActivate: [redirectSignedIn(STAFF, BACKOFFICE_LOGIN.home)],
    data: { login: BACKOFFICE_LOGIN },
    loadComponent: loadLogin,
  },
  {
    path: 'cms',
    canActivate: [requireRole(STAFF, '/cms/login')],
    loadComponent: () =>
      import('./features/backoffice/backoffice.layout').then((m) => m.BackofficeLayout),
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: () => homeSection(inject(SessionService).role()),
      },
      {
        path: 'clientes',
        loadComponent: () =>
          import('./features/backoffice/clientes/clientes.view').then((m) => m.ClientesView),
      },
      {
        path: 'cotizaciones',
        loadComponent: () =>
          import('./features/backoffice/cotizaciones/cotizaciones.view').then(
            (m) => m.CotizacionesView,
          ),
      },
      {
        path: 'cotizaciones/nueva',
        loadComponent: () =>
          import('./features/backoffice/cotizacion/asesor-cotizacion.view').then(
            (m) => m.AsesorCotizacionView,
          ),
      },
      {
        path: 'cotizaciones/:cotizacionId/emision',
        loadComponent: () =>
          import('./features/backoffice/emision/asesor-emision.view').then(
            (m) => m.AsesorEmisionView,
          ),
      },
      section('polizas'),
      section('avisos'),
    ],
  },
  {
    path: 'emision',
    canActivate: [requireRole(CUSTOMER, '/login')],
    loadComponent: () => import('./features/emision/emision.view').then((m) => m.EmisionView),
  },
  {
    path: '',
    canActivate: [requireRole(CUSTOMER, '/login')],
    loadComponent: () => import('./features/shell/shell.layout').then((m) => m.ShellLayout),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },
      {
        path: 'inicio',
        loadComponent: () => import('./features/inicio/inicio.view').then((m) => m.InicioView),
      },
      {
        path: 'polizas',
        loadComponent: () =>
          import('./features/polizas/lista/polizas-lista.view').then((m) => m.PolizasListaView),
      },
      {
        path: 'polizas/:numero',
        loadComponent: () =>
          import('./features/polizas/detalle/poliza-detalle.view').then((m) => m.PolizaDetalleView),
      },
      {
        path: 'suscripcion-rechazada',
        loadComponent: () =>
          import('./features/emision/rechazada/suscripcion-rechazada.view').then(
            (m) => m.SuscripcionRechazadaView,
          ),
      },
      {
        path: 'cotizacion',
        loadComponent: () =>
          import('./features/cotizacion/nueva/nueva-cotizacion.view').then(
            (m) => m.NuevaCotizacionView,
          ),
      },
      {
        path: 'cotizaciones/:cotizacionId',
        loadComponent: () =>
          import('./features/cotizacion/oferta/ver-oferta.view').then((m) => m.VerOfertaView),
      },
      destino('emision/:id', 'emision'),
      destino('siniestros/:id', 'siniestro'),
      destino('vida-crediticia', 'vidaCrediticia'),
    ],
  },
];
