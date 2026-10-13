import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { Conversation, Message, Source } from '../models/api.models';
import { AuthService } from './auth.service';

export type ChatStreamEvent =
  | { type: 'start'; data: { user_message: Message; conversation: { id: string; title: string } } }
  | { type: 'sources'; data: { sources: Source[] } }
  | { type: 'delta'; data: { text: string } }
  | { type: 'done'; data: { assistant_message: Message } }
  | { type: 'error'; data: { message: string; assistant_message?: Message } };

@Injectable({ providedIn: 'root' })
export class ConversationApi {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);

  list() {
    return firstValueFrom(this.http.get<Conversation[]>('/api/conversations'));
  }

  create(title?: string) {
    return firstValueFrom(this.http.post<Conversation>('/api/conversations', { title }));
  }

  rename(id: string, title: string) {
    return firstValueFrom(this.http.patch<Conversation>(`/api/conversations/${id}`, { title }));
  }

  remove(id: string) {
    return firstValueFrom(this.http.delete<void>(`/api/conversations/${id}`));
  }

  messages(id: string) {
    return firstValueFrom(this.http.get<Message[]>(`/api/conversations/${id}/messages`));
  }

  /** Envia a pergunta e lê a resposta em streaming (Server-Sent Events via fetch). */
  async *send(id: string, content: string, signal: AbortSignal): AsyncGenerator<ChatStreamEvent> {
    const response = await fetch(`/api/conversations/${id}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        Authorization: `Bearer ${this.auth.token}`,
      },
      body: JSON.stringify({ content }),
      signal,
    });
    if (response.status === 401) {
      this.auth.logout();
      throw new Error('Sessão expirada.');
    }
    if (!response.ok || !response.body) {
      const body = await response.json().catch(() => null);
      throw new Error(body?.detail ?? `Erro ${response.status} ao enviar a mensagem.`);
    }

    const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += value;
      let boundary: number;
      while ((boundary = buffer.indexOf('\n\n')) >= 0) {
        const raw = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const event = parseSse(raw);
        if (event) yield event;
      }
    }
  }
}

function parseSse(raw: string): ChatStreamEvent | null {
  let type = 'message';
  const data: string[] = [];
  for (const line of raw.split('\n')) {
    if (line.startsWith('event:')) type = line.slice(6).trim();
    else if (line.startsWith('data:')) data.push(line.slice(5).trim());
  }
  if (!data.length) return null;
  return { type, data: JSON.parse(data.join('\n')) } as ChatStreamEvent;
}
