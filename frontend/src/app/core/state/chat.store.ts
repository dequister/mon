import { computed, inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';

import { Conversation, Message } from '../models/api.models';
import { apiErrorMessage } from '../services/api-error';
import { ConversationApi } from '../services/conversation-api.service';
import { ToastService } from '../services/toast.service';

export interface ChatMessageView extends Message {
  streaming?: boolean;
}

/** Facade do chat: estado das conversas e mensagens em signals. */
@Injectable({ providedIn: 'root' })
export class ChatStore {
  private readonly api = inject(ConversationApi);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);
  private abort: AbortController | null = null;

  readonly conversations = signal<Conversation[]>([]);
  readonly activeId = signal<string | null>(null);
  readonly messages = signal<ChatMessageView[]>([]);
  readonly loadingMessages = signal(false);
  readonly streaming = signal(false);

  readonly activeConversation = computed(
    () => this.conversations().find((c) => c.id === this.activeId()) ?? null,
  );

  async loadConversations(): Promise<void> {
    try {
      this.conversations.set(await this.api.list());
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  async open(id: string | null): Promise<void> {
    if (id === this.activeId()) return;
    this.stop();
    this.activeId.set(id);
    this.messages.set([]);
    if (!id) return;
    this.loadingMessages.set(true);
    try {
      const messages = await this.api.messages(id);
      if (this.activeId() === id) this.messages.set(messages);
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
      this.router.navigate(['/']);
    } finally {
      this.loadingMessages.set(false);
    }
  }

  startNew(): void {
    this.stop();
    this.activeId.set(null);
    this.messages.set([]);
    this.router.navigate(['/']);
  }

  async send(content: string): Promise<void> {
    const question = content.trim();
    if (!question || this.streaming()) return;

    let conversationId = this.activeId();
    if (!conversationId) {
      try {
        const conversation = await this.api.create();
        conversationId = conversation.id;
        this.conversations.update((list) => [conversation, ...list]);
        this.activeId.set(conversation.id);
        this.router.navigate(['/c', conversation.id], { replaceUrl: true });
      } catch (error) {
        this.toast.error(apiErrorMessage(error));
        return;
      }
    }

    const now = new Date().toISOString();
    const tempUserId = `tmp-user-${Date.now()}`;
    const tempAssistantId = `tmp-assistant-${Date.now()}`;
    this.messages.update((list) => [
      ...list,
      this.draft(tempUserId, conversationId!, 'user', question, now),
      { ...this.draft(tempAssistantId, conversationId!, 'assistant', '', now), streaming: true },
    ]);

    this.streaming.set(true);
    this.abort = new AbortController();
    try {
      for await (const event of this.api.send(conversationId, question, this.abort.signal)) {
        switch (event.type) {
          case 'start':
            this.replace(tempUserId, event.data.user_message);
            this.touchConversation(event.data.conversation.id, event.data.conversation.title);
            break;
          case 'sources':
            this.patch(tempAssistantId, { sources: event.data.sources });
            break;
          case 'delta':
            this.patch(tempAssistantId, (m) => ({ content: m.content + event.data.text }));
            break;
          case 'done':
            this.replace(tempAssistantId, event.data.assistant_message);
            break;
          case 'error':
            if (event.data.assistant_message) this.replace(tempAssistantId, event.data.assistant_message);
            else this.patch(tempAssistantId, { error: event.data.message, streaming: false });
            break;
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        this.patch(tempAssistantId, { error: apiErrorMessage(error), streaming: false });
      }
    } finally {
      this.patch(tempAssistantId, { streaming: false });
      this.streaming.set(false);
      this.abort = null;
    }
  }

  stop(): void {
    this.abort?.abort();
  }

  async rename(id: string, title: string): Promise<void> {
    try {
      const updated = await this.api.rename(id, title);
      this.conversations.update((list) => list.map((c) => (c.id === id ? updated : c)));
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  async remove(id: string): Promise<void> {
    try {
      await this.api.remove(id);
      this.conversations.update((list) => list.filter((c) => c.id !== id));
      if (this.activeId() === id) this.startNew();
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  reset(): void {
    this.stop();
    this.conversations.set([]);
    this.messages.set([]);
    this.activeId.set(null);
  }

  private touchConversation(id: string, title: string): void {
    this.conversations.update((list) => {
      const current = list.find((c) => c.id === id);
      const updated = { ...(current as Conversation), id, title, updated_at: new Date().toISOString() };
      return [updated, ...list.filter((c) => c.id !== id)];
    });
  }

  private replace(id: string, message: Message): void {
    this.messages.update((list) => list.map((m) => (m.id === id ? { ...message, streaming: false } : m)));
  }

  private patch(
    id: string,
    change: Partial<ChatMessageView> | ((message: ChatMessageView) => Partial<ChatMessageView>),
  ): void {
    this.messages.update((list) =>
      list.map((m) => (m.id === id ? { ...m, ...(typeof change === 'function' ? change(m) : change) } : m)),
    );
  }

  private draft(id: string, conversationId: string, role: 'user' | 'assistant', content: string, at: string): ChatMessageView {
    return { id, conversation_id: conversationId, role, content, sources: [], details: {}, error: null, created_at: at };
  }
}
