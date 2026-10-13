import { JsonPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Job, JobDetail, JobStatus, JobType } from '../../../core/models/api.models';
import { AdminApi } from '../../../core/services/admin-api.service';
import { apiErrorMessage } from '../../../core/services/api-error';
import { ConfirmService } from '../../../core/services/confirm.service';
import { ToastService } from '../../../core/services/toast.service';
import { Icon } from '../../../shared/components/icon';
import { DateTimePipe, DurationPipe, Percent100Pipe, RelativeTimePipe } from '../../../shared/pipes/format.pipes';

export const JOB_STATUS: Record<JobStatus, { label: string; tone: string; icon: string }> = {
  queued: { label: 'Na fila', tone: 'info', icon: 'clock' },
  running: { label: 'Executando', tone: 'warning', icon: 'play' },
  succeeded: { label: 'Concluído', tone: 'success', icon: 'check-circle' },
  failed: { label: 'Falhou', tone: 'danger', icon: 'x-circle' },
  canceled: { label: 'Cancelado', tone: '', icon: 'x' },
};

export const JOB_TYPES: Record<JobType, { label: string; icon: string }> = {
  ingest_document: { label: 'Indexação de documento', icon: 'file-text' },
  sync_folder: { label: 'Sincronização da pasta', icon: 'folder-sync' },
  reindex_all: { label: 'Reindexação geral', icon: 'refresh' },
  eval_run: { label: 'Avaliação do RAG', icon: 'flask' },
  eval_generate: { label: 'Geração de casos de teste', icon: 'sparkles' },
};

@Component({
  selector: 'app-jobs-page',
  imports: [FormsModule, JsonPipe, Icon, DateTimePipe, DurationPipe, Percent100Pipe, RelativeTimePipe],
  templateUrl: './jobs-page.html',
  styleUrl: './jobs-page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class JobsPage implements OnInit {
  private readonly api = inject(AdminApi);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);

  protected readonly jobs = signal<Job[]>([]);
  protected readonly stats = signal<Record<string, number>>({});
  protected readonly loading = signal(true);
  protected readonly selected = signal<JobDetail | null>(null);
  protected statusFilter = '';
  protected typeFilter = '';

  protected readonly statusInfo = JOB_STATUS;
  protected readonly typeInfo = JOB_TYPES;
  protected readonly typeOptions = Object.entries(JOB_TYPES);
  protected readonly active = computed(() => (this.stats()['queued'] ?? 0) + (this.stats()['running'] ?? 0));

  constructor() {
    const timer = setInterval(() => this.refresh(false), 3000);
    inject(DestroyRef).onDestroy(() => clearInterval(timer));
  }

  ngOnInit(): void {
    this.refresh();
  }

  async refresh(showLoading = true): Promise<void> {
    if (showLoading) this.loading.set(true);
    try {
      const [jobs, stats] = await Promise.all([this.api.jobs(this.statusFilter, this.typeFilter), this.api.jobStats()]);
      this.jobs.set(jobs);
      this.stats.set(stats);
      const selected = this.selected();
      if (selected) this.selected.set(await this.api.job(selected.id));
    } catch (error) {
      if (showLoading) this.toast.error(apiErrorMessage(error));
    } finally {
      this.loading.set(false);
    }
  }

  protected async open(job: Job): Promise<void> {
    if (this.selected()?.id === job.id) {
      this.selected.set(null);
      return;
    }
    try {
      this.selected.set(await this.api.job(job.id));
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected async syncFolder(): Promise<void> {
    try {
      await this.api.syncFolder();
      this.toast.success('Sincronização da pasta agendada.');
      this.refresh(false);
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected async reindexAll(): Promise<void> {
    const ok = await this.confirm.ask({
      title: 'Reindexar todos os documentos',
      message:
        'Todos os documentos serão processados novamente. Os vetores antigos só são removidos após o sucesso de cada reindexação.',
      confirmText: 'Reindexar tudo',
    });
    if (!ok) return;
    try {
      await this.api.reindexAll();
      this.toast.success('Reindexação geral agendada.');
      this.refresh(false);
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected async cancel(job: Job, event: Event): Promise<void> {
    event.stopPropagation();
    try {
      await this.api.cancelJob(job.id);
      this.refresh(false);
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected async retry(job: Job, event: Event): Promise<void> {
    event.stopPropagation();
    try {
      await this.api.retryJob(job.id);
      this.toast.success('Job reenviado para a fila.');
      this.refresh(false);
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected target(job: Job): string {
    const payload = job.payload as Record<string, string>;
    const result = (job.result ?? {}) as Record<string, unknown>;
    if (job.type === 'ingest_document') return payload['filename'] ?? (result['filename'] as string) ?? '';
    if (job.type === 'eval_generate') return `${payload['count'] ?? ''} casos`;
    return '';
  }
}
