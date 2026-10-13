import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { ConfirmService } from '../../core/services/confirm.service';
import { ToastService } from '../../core/services/toast.service';
import { Icon } from './icon';

/** Notificações flutuantes. */
@Component({
  selector: 'app-toasts',
  imports: [Icon],
  template: `
    <div class="toasts" aria-live="polite">
      @for (toast of toasts.toasts(); track toast.id) {
        <div class="toast" [class]="toast.kind" role="status">
          <app-icon [name]="toast.kind === 'success' ? 'check-circle' : toast.kind === 'error' ? 'alert' : 'info'" />
          <span class="grow">{{ toast.text }}</span>
          <button class="close" (click)="toasts.dismiss(toast.id)" aria-label="Fechar">
            <app-icon name="x" [size]="14" />
          </button>
        </div>
      }
    </div>
  `,
  styles: `
    .toasts { position: fixed; top: 16px; right: 16px; z-index: 200; display: flex; flex-direction: column; gap: 8px; width: min(380px, calc(100vw - 32px)); }
    .toast { display: flex; align-items: flex-start; gap: 10px; padding: 12px 14px; border-radius: 12px; background: #fff; border: 1px solid var(--border); box-shadow: var(--shadow); animation: pop .18s ease; font-weight: 500; }
    .toast.success app-icon { color: var(--success); }
    .toast.error { border-color: #f5c2c2; }
    .toast.error app-icon { color: var(--danger); }
    .toast.info app-icon { color: var(--info); }
    .close { border: none; background: none; color: var(--muted); cursor: pointer; padding: 2px; }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Toasts {
  protected readonly toasts = inject(ToastService);
}

/** Diálogo de confirmação global. */
@Component({
  selector: 'app-confirm-dialog',
  template: `
    @if (confirm.pending(); as dialog) {
      <div class="modal-backdrop" (click)="confirm.close(false)">
        <div class="modal" role="dialog" aria-modal="true" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>{{ dialog.title }}</h3>
            <p>{{ dialog.message }}</p>
          </div>
          <div class="modal-body"></div>
          <div class="modal-footer">
            <button class="btn" (click)="confirm.close(false)">Cancelar</button>
            <button class="btn" [class.primary]="!dialog.danger" [class.danger-solid]="dialog.danger" (click)="confirm.close(true)">
              {{ dialog.confirmText ?? 'Confirmar' }}
            </button>
          </div>
        </div>
      </div>
    }
  `,
  styles: `
    .modal { width: min(440px, 100%); }
    .danger-solid { background: var(--danger); border-color: var(--danger); color: #fff; }
    .danger-solid:hover { background: #b91c1c !important; border-color: #b91c1c !important; }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConfirmDialog {
  protected readonly confirm = inject(ConfirmService);
}
