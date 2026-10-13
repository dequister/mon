import { HttpEventType } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { DocumentItem, DocumentStats, DocumentStatus, UploadItem } from '../../../core/models/api.models';
import { AdminApi } from '../../../core/services/admin-api.service';
import { apiErrorMessage } from '../../../core/services/api-error';
import { ConfirmService } from '../../../core/services/confirm.service';
import { DownloadService } from '../../../core/services/download.service';
import { ToastService } from '../../../core/services/toast.service';
import { fileIcon, Icon } from '../../../shared/components/icon';
import { DateTimePipe, FileSizePipe, Percent100Pipe } from '../../../shared/pipes/format.pipes';

interface UploadTask {
  id: number;
  name: string;
  size: number;
  progress: number;
  state: 'uploading' | 'done' | 'error';
  result?: UploadItem;
  error?: string;
}

export const STATUS_LABELS: Record<DocumentStatus, { label: string; tone: string }> = {
  pending: { label: 'Na fila', tone: 'info' },
  processing: { label: 'Processando', tone: 'warning' },
  indexed: { label: 'Indexado', tone: 'success' },
  failed: { label: 'Falhou', tone: 'danger' },
};

const UPLOAD_LABELS: Record<UploadItem['status'], { label: string; tone: string }> = {
  created: { label: 'Enviado', tone: 'success' },
  updated: { label: 'Nova versão', tone: 'primary' },
  duplicate: { label: 'Duplicado', tone: 'warning' },
  rejected: { label: 'Rejeitado', tone: 'danger' },
};

@Component({
  selector: 'app-documents-page',
  imports: [FormsModule, Icon, FileSizePipe, DateTimePipe, Percent100Pipe],
  templateUrl: './documents-page.html',
  styleUrl: './documents-page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DocumentsPage implements OnInit {
  private readonly api = inject(AdminApi);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly downloads = inject(DownloadService);
  private nextUploadId = 1;

  protected readonly documents = signal<DocumentItem[]>([]);
  protected readonly stats = signal<DocumentStats | null>(null);
  protected readonly uploads = signal<UploadTask[]>([]);
  protected readonly loading = signal(true);
  protected readonly dragOver = signal(false);
  protected readonly expandedId = signal<string | null>(null);
  protected query = '';
  protected statusFilter = '';

  protected readonly statusLabels = STATUS_LABELS;
  protected readonly uploadLabels = UPLOAD_LABELS;
  protected readonly fileIcon = fileIcon;

  protected readonly accept = computed(() => (this.stats()?.supported_extensions ?? []).join(','));
  protected readonly busy = computed(() =>
    this.documents().some((d) => d.status === 'pending' || d.status === 'processing'),
  );

  constructor() {
    // Atualiza a lista enquanto houver documentos em processamento.
    const timer = setInterval(() => {
      if (this.busy()) this.refresh(false);
    }, 4000);
    inject(DestroyRef).onDestroy(() => clearInterval(timer));
  }

  ngOnInit(): void {
    this.refresh();
  }

  async refresh(showLoading = true): Promise<void> {
    if (showLoading) this.loading.set(true);
    try {
      const [documents, stats] = await Promise.all([
        this.api.documents(this.query, this.statusFilter),
        this.api.documentStats(),
      ]);
      this.documents.set(documents);
      this.stats.set(stats);
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    } finally {
      this.loading.set(false);
    }
  }

  protected onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(true);
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(false);
    this.enqueue(Array.from(event.dataTransfer?.files ?? []));
  }

  protected onPick(input: HTMLInputElement): void {
    this.enqueue(Array.from(input.files ?? []));
    input.value = '';
  }

  protected clearUploads(): void {
    this.uploads.update((list) => list.filter((task) => task.state === 'uploading'));
  }

  private enqueue(files: File[]): void {
    for (const file of files) this.upload(file);
  }

  private upload(file: File): void {
    const id = this.nextUploadId++;
    this.uploads.update((list) => [{ id, name: file.name, size: file.size, progress: 0, state: 'uploading' }, ...list]);
    const update = (change: Partial<UploadTask>) =>
      this.uploads.update((list) => list.map((task) => (task.id === id ? { ...task, ...change } : task)));

    this.api.upload(file).subscribe({
      next: (event) => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          update({ progress: event.loaded / event.total });
        } else if (event.type === HttpEventType.Response) {
          const result = event.body?.[0];
          update({ progress: 1, state: result?.status === 'rejected' ? 'error' : 'done', result, error: result?.status === 'rejected' ? result.message : undefined });
          this.refresh(false);
        }
      },
      error: (error) => update({ state: 'error', error: apiErrorMessage(error) }),
    });
  }

  protected toggle(document: DocumentItem): void {
    this.expandedId.update((current) => (current === document.id ? null : document.id));
  }

  protected async reindex(document: DocumentItem, event: Event): Promise<void> {
    event.stopPropagation();
    try {
      await this.api.reindexDocument(document.id);
      this.toast.success(`Reindexação de "${document.filename}" agendada.`);
      this.refresh(false);
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected async remove(document: DocumentItem, event: Event): Promise<void> {
    event.stopPropagation();
    const ok = await this.confirm.ask({
      title: 'Excluir documento',
      message: `"${document.filename}" será removido da base, incluindo todos os seus vetores no Qdrant.`,
      confirmText: 'Excluir',
      danger: true,
    });
    if (!ok) return;
    try {
      await this.api.deleteDocument(document.id);
      this.toast.success('Documento excluído.');
      this.refresh(false);
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected download(document: DocumentItem, event: Event): void {
    event.stopPropagation();
    this.downloads.document(document.id, document.filename);
  }

  protected countBy(status: DocumentStatus): number {
    return this.stats()?.by_status?.[status] ?? 0;
  }
}
