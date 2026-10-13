import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** Marca do Mon. */
@Component({
  selector: 'app-mon-logo',
  template: `
    <svg [attr.width]="size()" [attr.height]="size()" viewBox="0 0 64 64" aria-hidden="true">
      <defs>
        <linearGradient id="mon-gradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#6366f1" />
          <stop offset="1" stop-color="#14b8a6" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="16" fill="url(#mon-gradient)" />
      <path d="M16 46V20l16 15 16-15v26" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
  `,
  styles: `:host { display: inline-flex; flex: none; }`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MonLogo {
  readonly size = input(32);
}
