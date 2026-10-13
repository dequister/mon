import { Injectable, signal } from '@angular/core';

export interface ConfirmOptions {
  title: string;
  message: string;
  confirmText?: string;
  danger?: boolean;
}

interface PendingConfirm extends ConfirmOptions {
  resolve: (value: boolean) => void;
}

/** Diálogo de confirmação baseado em Promise (substitui window.confirm). */
@Injectable({ providedIn: 'root' })
export class ConfirmService {
  readonly pending = signal<PendingConfirm | null>(null);

  ask(options: ConfirmOptions): Promise<boolean> {
    return new Promise((resolve) => this.pending.set({ ...options, resolve }));
  }

  close(result: boolean): void {
    this.pending()?.resolve(result);
    this.pending.set(null);
  }
}
