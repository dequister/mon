import { ChangeDetectionStrategy, Component, ElementRef, input, output, signal, viewChild } from '@angular/core';

import { Icon } from '../../shared/components/icon';

/** Caixa de mensagem: Enter envia, Shift+Enter quebra linha. */
@Component({
  selector: 'app-composer',
  imports: [Icon],
  template: `
    <form class="composer" (submit)="$event.preventDefault(); submit()">
      <textarea
        #box
        rows="1"
        placeholder="Pergunte algo ao Mon…"
        [value]="text()"
        (input)="onInput(box)"
        (keydown.enter)="onEnter($any($event))"
        aria-label="Mensagem"
      ></textarea>
      @if (busy()) {
        <button type="button" class="send stop" (click)="stopped.emit()" title="Parar resposta" aria-label="Parar resposta">
          <app-icon name="stop" [size]="16" />
        </button>
      } @else {
        <button type="submit" class="send" [disabled]="!text().trim()" title="Enviar" aria-label="Enviar">
          <app-icon name="arrow-up" [size]="18" [stroke]="2.4" />
        </button>
      }
    </form>
  `,
  styles: `
    .composer { display: flex; align-items: flex-end; gap: 10px; padding: 10px 10px 10px 18px; background: var(--surface); border: 1px solid var(--border); border-radius: 18px; box-shadow: var(--shadow); transition: border-color .15s, box-shadow .15s; }
    .composer:focus-within { border-color: #c7c9f5; box-shadow: 0 0 0 4px var(--primary-50), var(--shadow); }
    textarea { flex: 1; border: none; outline: none; resize: none; background: transparent; font-size: 15px; line-height: 1.5; max-height: 220px; padding: 7px 0; }
    .send { width: 38px; height: 38px; border-radius: 12px; border: none; background: var(--primary); color: #fff; display: grid; place-items: center; cursor: pointer; flex: none; transition: background .15s, opacity .15s; }
    .send:hover:not(:disabled) { background: var(--primary-600); }
    .send:disabled { opacity: .35; cursor: not-allowed; }
    .send.stop { background: var(--text); }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Composer {
  readonly busy = input(false);
  readonly submitted = output<string>();
  readonly stopped = output<void>();

  protected readonly text = signal('');
  private readonly box = viewChild.required<ElementRef<HTMLTextAreaElement>>('box');

  protected onInput(element: HTMLTextAreaElement): void {
    this.text.set(element.value);
    this.autosize();
  }

  protected onEnter(event: KeyboardEvent): void {
    if (event.shiftKey || event.isComposing) return;
    event.preventDefault();
    this.submit();
  }

  protected submit(): void {
    const value = this.text().trim();
    if (!value || this.busy()) return;
    this.submitted.emit(value);
    this.text.set('');
    this.box().nativeElement.value = '';
    this.autosize();
  }

  private autosize(): void {
    const element = this.box().nativeElement;
    element.style.height = 'auto';
    element.style.height = `${Math.min(element.scrollHeight, 220)}px`;
  }
}
