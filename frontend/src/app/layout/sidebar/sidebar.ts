import { ChangeDetectionStrategy, Component, computed, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { Conversation } from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { ConfirmService } from '../../core/services/confirm.service';
import { ChatStore } from '../../core/state/chat.store';
import { Icon } from '../../shared/components/icon';
import { MonLogo } from '../../shared/components/mon-logo';

interface ConversationGroup {
  label: string;
  items: Conversation[];
}

const ADMIN_LINKS = [
  { path: '/admin/documentos', icon: 'cloud-upload', label: 'Documentos' },
  { path: '/admin/jobs', icon: 'folder-sync', label: 'Jobs de sincronização' },
  { path: '/admin/avaliacao', icon: 'flask', label: 'Avaliação do RAG' },
  { path: '/admin/modelos', icon: 'cpu', label: 'Modelos e RAG' },
];

@Component({
  selector: 'app-sidebar',
  imports: [FormsModule, RouterLink, RouterLinkActive, Icon, MonLogo],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Sidebar {
  protected readonly store = inject(ChatStore);
  protected readonly auth = inject(AuthService);
  private readonly confirm = inject(ConfirmService);

  readonly navigated = output<void>();

  protected readonly adminLinks = ADMIN_LINKS;
  protected readonly search = signal('');
  protected readonly editingId = signal<string | null>(null);
  protected editingTitle = '';

  protected readonly initials = computed(() => {
    const user = this.auth.user();
    const name = user?.full_name || user?.username || '?';
    return name
      .split(' ')
      .map((part) => part[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  });

  protected readonly groups = computed<ConversationGroup[]>(() => {
    const term = this.search().trim().toLowerCase();
    const items = this.store.conversations().filter((c) => !term || c.title.toLowerCase().includes(term));
    const startOfToday = new Date();
    startOfToday.setHours(0, 0, 0, 0);
    const day = 86_400_000;
    const buckets: ConversationGroup[] = [
      { label: 'Hoje', items: [] },
      { label: 'Ontem', items: [] },
      { label: 'Últimos 7 dias', items: [] },
      { label: 'Mais antigas', items: [] },
    ];
    for (const conversation of items) {
      const time = new Date(conversation.updated_at).getTime();
      const index =
        time >= startOfToday.getTime() ? 0 : time >= startOfToday.getTime() - day ? 1 : time >= startOfToday.getTime() - 7 * day ? 2 : 3;
      buckets[index].items.push(conversation);
    }
    return buckets.filter((group) => group.items.length);
  });

  newChat(): void {
    this.store.startNew();
    this.navigated.emit();
  }

  startRename(conversation: Conversation, event: Event): void {
    event.stopPropagation();
    event.preventDefault();
    this.editingId.set(conversation.id);
    this.editingTitle = conversation.title;
  }

  async saveRename(conversation: Conversation): Promise<void> {
    const title = this.editingTitle.trim();
    this.editingId.set(null);
    if (title && title !== conversation.title) await this.store.rename(conversation.id, title);
  }

  async remove(conversation: Conversation, event: Event): Promise<void> {
    event.stopPropagation();
    event.preventDefault();
    const ok = await this.confirm.ask({
      title: 'Excluir conversa',
      message: `A conversa "${conversation.title}" e todas as suas mensagens serão excluídas.`,
      confirmText: 'Excluir',
      danger: true,
    });
    if (ok) await this.store.remove(conversation.id);
  }

  logout(): void {
    this.store.reset();
    this.auth.logout();
  }
}
