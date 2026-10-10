import { Routes } from '@angular/router';
import { redirectSignedIn, requireSession } from './core/session/session.guard';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [redirectSignedIn],
    loadComponent: () => import('./features/login/login.view').then((m) => m.LoginView),
  },
  {
    path: '',
    canActivate: [requireSession],
    loadComponent: () => import('./features/shell/shell.layout').then((m) => m.ShellLayout),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'user' },
      {
        path: 'user',
        loadComponent: () => import('./features/user/user.view').then((m) => m.UserView),
      },
      {
        path: 'cms',
        loadComponent: () => import('./features/cms/cms.view').then((m) => m.CmsView),
      },
    ],
  },
];
