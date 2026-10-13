import { NgTemplateOutlet } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';

import { Source } from '../../core/models/api.models';
import { DownloadService } from '../../core/services/download.service';
import { fileIcon, Icon } from '../../shared/components/icon';
import { Percent100Pipe } from '../../shared/pipes/format.pipes';

interface SourceGroup {
  documentId: string;
  filename: string;
  fileType: string;
  items: Source[];
  locations: string[];
  relevance: number;
  ocr: boolean;
}

function location(source: Source): string | null {
  if (source.sheet) return `planilha ${source.sheet}`;
  if (source.page) return ['pptx', 'ppt', 'odp'].includes(source.file_type) ? `slide ${source.page}` : `p. ${source.page}`;
  return null;
}

function group(sources: Source[]): SourceGroup[] {
  const map = new Map<string, SourceGroup>();
  for (const source of sources) {
    const key = source.document_id ?? source.filename;
    const entry =
      map.get(key) ??
      ({ documentId: source.document_id, filename: source.filename, fileType: source.file_type, items: [], locations: [], relevance: 0, ocr: false } as SourceGroup);
    entry.items.push(source);
    entry.relevance = Math.max(entry.relevance, source.rerank_score ?? source.vector_score ?? 0);
    entry.ocr ||= source.ocr;
    const loc = location(source);
    if (loc && !entry.locations.includes(loc)) entry.locations.push(loc);
    map.set(key, entry);
  }
  return [...map.values()];
}

/** Seção "Fontes consultadas" ao final de cada resposta do Mon. */
@Component({
  selector: 'app-sources-panel',
  imports: [NgTemplateOutlet, Icon, Percent100Pipe],
  templateUrl: './sources-panel.html',
  styleUrl: './sources-panel.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SourcesPanel {
  private readonly downloads = inject(DownloadService);

  readonly sources = input.required<Source[]>();
  readonly streaming = input(false);

  protected readonly expanded = signal<string | null>(null);
  protected readonly showOthers = signal(false);
  protected readonly fileIcon = fileIcon;

  protected readonly cited = computed(() => group(this.sources().filter((s) => s.cited)));
  protected readonly others = computed(() => group(this.sources().filter((s) => !s.cited)));

  protected toggle(id: string): void {
    this.expanded.update((current) => (current === id ? null : id));
  }

  protected download(item: SourceGroup, event: Event): void {
    event.stopPropagation();
    this.downloads.document(item.documentId, item.filename);
  }

  protected location = location;
}
