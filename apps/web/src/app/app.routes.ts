import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { redirectSignedIn, requireRole } from './core/session/session.guard';
import { Role, SessionService } from './core/session/session.service';
import { homeSection, Section } from './features/backoffice/sections';
import { BACKOFFICE_LOGIN, CUSTOMER_LOGIN } from './features/login/login.variant';

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

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [redirectSignedIn(CUSTOMER, CUSTOMER_LOGIN.home)],
    data: { login: CUSTOMER_LOGIN },
    loadComponent: loadLogin,
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
      section('cotizaciones'),
      section('polizas'),
      section('avisos'),
    ],
  },
  {
    path: '',
    canActivate: [requireRole(CUSTOMER, '/login')],
    loadComponent: () => import('./features/shell/shell.layout').then((m) => m.ShellLayout),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'user' },
      {
        path: 'user',
        loadComponent: () => import('./features/user/user.view').then((m) => m.UserView),
      },
    ],
  },
];
