import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { ConfirmDialog, Toasts } from './shared/components/overlays';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Toasts, ConfirmDialog],
  template: `
    <router-outlet />
    <app-toasts />
    <app-confirm-dialog />
  `,
})
export class App {}
