import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { ChatStore } from '../../core/state/chat.store';
import { AuthService } from '../../core/services/auth.service';
import { Icon } from '../../shared/components/icon';
import { MonLogo } from '../../shared/components/mon-logo';
import { Sidebar } from '../sidebar/sidebar';

@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, Sidebar, Icon, MonLogo],
  template: `
    <div class="shell" [class.menu-open]="menuOpen()">
      <app-sidebar class="sidebar" (navigated)="menuOpen.set(false)" />
      <div class="scrim" (click)="menuOpen.set(false)"></div>
      <main class="main">
        <header class="topbar">
          <button class="btn ghost icon" (click)="menuOpen.set(true)" aria-label="Abrir menu">
            <app-icon name="menu" />
          </button>
          <app-mon-logo [size]="26" />
          <strong>Mon</strong>
        </header>
        <div class="outlet"><router-outlet /></div>
      </main>
    </div>
  `,
  styles: `
    .shell { display: grid; grid-template-columns: 280px 1fr; height: 100vh; overflow: hidden; }
    .sidebar { min-height: 0; }
    .main { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
    .outlet { flex: 1; min-height: 0; }
    .topbar { display: none; align-items: center; gap: 10px; padding: 8px 12px; border-bottom: 1px solid var(--border); background: var(--surface); }
    .scrim { display: none; }
    @media (max-width: 900px) {
      .shell { grid-template-columns: 1fr; }
      .topbar { display: flex; }
      .sidebar { position: fixed; inset: 0 auto 0 0; width: 290px; z-index: 50; transform: translateX(-100%); transition: transform .2s ease; }
      .menu-open .sidebar { transform: none; box-shadow: var(--shadow-lg); }
      .menu-open .scrim { display: block; position: fixed; inset: 0; background: rgba(15, 18, 38, .4); z-index: 40; }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Shell implements OnInit {
  private readonly store = inject(ChatStore);
  private readonly auth = inject(AuthService);
  protected readonly menuOpen = signal(false);

  ngOnInit(): void {
    this.store.loadConversations();
    // Atualiza o papel do usuário caso tenha mudado no servidor.
    this.auth.refreshUser().catch(() => undefined);
  }
}
