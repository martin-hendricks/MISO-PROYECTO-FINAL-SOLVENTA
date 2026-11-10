import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { redirectSignedIn, requireLocaleChosen, requireRole } from './core/session/session.guard';
import { Role, SessionService } from './core/session/session.service';
import { homeSection } from './features/backoffice/sections';
import type { Destino } from './features/destino/destino.view';
import { BACKOFFICE_LOGIN, CUSTOMER_LOGIN } from './features/login/login.variant';
import { requireDraft } from './features/registro/registro.draft';

const CUSTOMER: readonly Role[] = ['cliente'];
const STAFF: readonly Role[] = ['asesor', 'operador'];

const loadLogin = () => import('./features/login/login.view').then((m) => m.LoginView);
const destino = (path: string, name: Destino) => ({
  path,
  data: { destino: name },
  loadComponent: () => import('./features/destino/destino.view').then((m) => m.DestinoView),
});

export const routes: Routes = [
  {
    path: 'idioma-region',
    canActivate: [redirectSignedIn(CUSTOMER, CUSTOMER_LOGIN.home)],
    loadComponent: () =>
      import('./features/idioma-region/idioma-region.view').then((m) => m.IdiomaRegionView),
  },
  {
    // HU-108's gate is only on sign-up ("Continuar sigue a registro"): a
    // returning customer going straight to /login to sign in is not a
    // "first launch" and must not be stopped here.
    path: 'login',
    canActivate: [redirectSignedIn(CUSTOMER, CUSTOMER_LOGIN.home)],
    data: { login: CUSTOMER_LOGIN },
    loadComponent: loadLogin,
  },
  {
    path: 'registro',
    canActivate: [redirectSignedIn(CUSTOMER, CUSTOMER_LOGIN.home), requireLocaleChosen],
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
      {
        path: 'polizas',
        loadComponent: () =>
          import('./features/backoffice/polizas/poliza-backoffice-detalle.view').then(
            (m) => m.PolizaBackofficeDetalleView,
          ),
      },
      {
        path: 'polizas/:numero',
        loadComponent: () =>
          import('./features/backoffice/polizas/poliza-backoffice-detalle.view').then(
            (m) => m.PolizaBackofficeDetalleView,
          ),
      },
      {
        path: 'avisos',
        loadComponent: () =>
          import('./features/backoffice/avisos/avisos.view').then((m) => m.AvisosView),
      },
      {
        path: 'reportes',
        loadComponent: () =>
          import('./features/backoffice/reportes/reportes.view').then((m) => m.ReportesView),
      },
      {
        path: 'metricas',
        loadComponent: () =>
          import('./features/backoffice/metricas/metricas.view').then((m) => m.MetricasView),
      },
      {
        path: 'notificaciones',
        loadComponent: () =>
          import('./features/backoffice/notificaciones/notificaciones.view').then(
            (m) => m.NotificacionesView,
          ),
      },
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
        // HU-119: ruta literal antes de polizas/:numero -- "avisos" no es un numero de poliza.
        path: 'polizas/avisos',
        loadComponent: () =>
          import('./features/polizas/avisos/polizas-avisos.view').then(
            (m) => m.PolizasAvisosView,
          ),
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
      {
        path: 'confirmacion-tarjeta',
        loadComponent: () =>
          import('./features/emision/confirmacion-tarjeta/confirmacion-tarjeta.view').then(
            (m) => m.ConfirmacionTarjetaView,
          ),
      },
      destino('emision/:id', 'emision'),
      {
        path: 'siniestros',
        loadComponent: () =>
          import('./features/siniestros/lista/siniestros-lista.view').then(
            (m) => m.SiniestrosListaView,
          ),
      },
      {
        // Rutas literales antes de siniestros/:id: "nuevo" y "parametrico" no son ids.
        path: 'siniestros/nuevo',
        loadComponent: () =>
          import('./features/siniestros/reportar/reportar-siniestro.view').then(
            (m) => m.ReportarSiniestroView,
          ),
      },
      {
        path: 'siniestros/parametrico',
        loadComponent: () =>
          import('./features/siniestros/parametrico/parametrico.view').then(
            (m) => m.ParametricoView,
          ),
      },
      {
        path: 'siniestros/:id',
        loadComponent: () =>
          import('./features/siniestros/detalle/siniestro-detalle.view').then(
            (m) => m.SiniestroDetalleView,
          ),
      },
      {
        path: 'billetera',
        loadComponent: () =>
          import('./features/billetera/lista/billetera-lista.view').then((m) => m.BilleteraListaView),
      },
      {
        path: 'billetera/:id',
        loadComponent: () =>
          import('./features/billetera/detalle/billetera-detalle.view').then(
            (m) => m.BilleteraDetalleView,
          ),
      },
      destino('perfil', 'perfil'),
      {
        path: 'vida-crediticia',
        loadComponent: () =>
          import('./features/vida-crediticia/vida-crediticia.view').then(
            (m) => m.VidaCrediticiaView,
          ),
      },
    ],
  },
];
