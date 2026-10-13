import { Routes } from '@angular/router';

import { adminGuard, authGuard, guestGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    title: 'Entrar · Mon',
    loadComponent: () => import('./features/auth/login').then((m) => m.LoginPage),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./layout/shell/shell').then((m) => m.Shell),
    children: [
      {
        path: '',
        title: 'Mon',
        loadComponent: () => import('./features/chat/chat-page').then((m) => m.ChatPage),
      },
      {
        path: 'c/:id',
        title: 'Mon',
        loadComponent: () => import('./features/chat/chat-page').then((m) => m.ChatPage),
      },
      {
        path: 'admin',
        canActivate: [adminGuard],
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'documentos' },
          {
            path: 'documentos',
            title: 'Documentos · Mon',
            loadComponent: () => import('./features/admin/documents/documents-page').then((m) => m.DocumentsPage),
          },
          {
            path: 'jobs',
            title: 'Jobs · Mon',
            loadComponent: () => import('./features/admin/jobs/jobs-page').then((m) => m.JobsPage),
          },
          {
            path: 'avaliacao',
            title: 'Avaliação · Mon',
            loadComponent: () => import('./features/admin/evals/evals-page').then((m) => m.EvalsPage),
          },
          {
            path: 'modelos',
            title: 'Modelos · Mon',
            loadComponent: () => import('./features/admin/models/models-page').then((m) => m.ModelsPage),
          },
        ],
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
