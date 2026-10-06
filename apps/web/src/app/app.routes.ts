import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'user' },
  {
    path: 'user',
    loadComponent: () => import('./features/user/user.view').then((m) => m.UserView),
  },
  {
    path: 'cms',
    loadComponent: () => import('./features/cms/cms.view').then((m) => m.CmsView),
  },
];
