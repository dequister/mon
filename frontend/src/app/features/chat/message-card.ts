import { ChangeDetectionStrategy, Component, computed, input, signal } from '@angular/core';

import { ChatMessageView } from '../../core/state/chat.store';
import { Icon } from '../../shared/components/icon';
import { MonLogo } from '../../shared/components/mon-logo';
import { MarkdownPipe } from '../../shared/pipes/markdown.pipe';
import { SourcesPanel } from './sources-panel';

@Component({
  selector: 'app-message-card',
  imports: [Icon, MonLogo, MarkdownPipe, SourcesPanel],
  templateUrl: './message-card.html',
  styleUrl: './message-card.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MessageCard {
  readonly message = input.required<ChatMessageView>();

  protected readonly copied = signal(false);
  protected readonly showDetails = signal(false);

  protected readonly modelLabel = computed(() => this.message().details?.model ?? null);
  protected readonly latency = computed(() => {
    const ms = this.message().details?.latency_ms;
    return ms ? `${(ms / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}s` : null;
  });
  protected readonly timings = computed(() => Object.entries(this.message().details?.timings_ms ?? {}));

  protected async copy(): Promise<void> {
    await navigator.clipboard.writeText(this.message().content);
    this.copied.set(true);
    setTimeout(() => this.copied.set(false), 1500);
  }
}
