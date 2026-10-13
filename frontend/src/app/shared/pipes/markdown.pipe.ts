import { inject, Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import DOMPurify from 'dompurify';
import { marked } from 'marked';

marked.setOptions({ gfm: true, breaks: true });

/** Converte Markdown em HTML sanitizado e destaca citações [n]. */
@Pipe({ name: 'markdown' })
export class MarkdownPipe implements PipeTransform {
  private readonly sanitizer = inject(DomSanitizer);

  transform(value: string | null | undefined): SafeHtml {
    if (!value) return '';
    const html = marked.parse(value, { async: false }) as string;
    const withCitations = html.replace(
      /\[(\d{1,2})\](?!\()/g,
      '<sup class="cite" data-cite="$1">$1</sup>',
    );
    const clean = DOMPurify.sanitize(withCitations, { ADD_ATTR: ['target', 'data-cite'] });
    // HTML já sanitizado pelo DOMPurify.
    return this.sanitizer.bypassSecurityTrustHtml(clean);
  }
}
