import {
  afterRenderEffect,
  ChangeDetectionStrategy,
  Component,
  effect,
  ElementRef,
  inject,
  input,
  untracked,
  viewChild,
} from '@angular/core';

import { AuthService } from '../../core/services/auth.service';
import { ChatStore } from '../../core/state/chat.store';
import { MonLogo } from '../../shared/components/mon-logo';
import { Composer } from './composer';
import { MessageCard } from './message-card';

const SUGGESTIONS = [
  'Quais documentos são necessários para a matrícula?',
  'Como funciona o trancamento de disciplinas?',
  'Qual a carga horária mínima do estágio supervisionado?',
  'Resuma o calendário acadêmico do semestre.',
];

@Component({
  selector: 'app-chat-page',
  imports: [MessageCard, Composer, MonLogo],
  templateUrl: './chat-page.html',
  styleUrl: './chat-page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChatPage {
  protected readonly store = inject(ChatStore);
  protected readonly auth = inject(AuthService);
  protected readonly suggestions = SUGGESTIONS;

  /** Parâmetro de rota :id (ligado via withComponentInputBinding). */
  readonly id = input<string | undefined>();

  private readonly scroller = viewChild<ElementRef<HTMLElement>>('scroller');

  constructor() {
    effect(() => {
      const id = this.id() ?? null;
      untracked(() => this.store.open(id));
    });

    // Mantém a rolagem no fim enquanto a resposta chega.
    afterRenderEffect(() => {
      this.store.messages();
      const element = this.scroller()?.nativeElement;
      if (!element) return;
      const nearBottom = element.scrollHeight - element.scrollTop - element.clientHeight < 160;
      if (nearBottom || this.store.streaming()) element.scrollTop = element.scrollHeight;
    });
  }

  protected firstName(): string {
    const user = this.auth.user();
    return (user?.full_name || user?.username || '').split(' ')[0];
  }

  protected send(text: string): void {
    this.store.send(text);
  }
}
