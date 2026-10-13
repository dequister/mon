import { ChangeDetectionStrategy, Component, computed, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { EvalCase, EvalCaseInput, EvalMetrics, EvalResult, EvalRun, EvalRunDetail } from '../../../core/models/api.models';
import { AdminApi } from '../../../core/services/admin-api.service';
import { apiErrorMessage } from '../../../core/services/api-error';
import { ConfirmService } from '../../../core/services/confirm.service';
import { ToastService } from '../../../core/services/toast.service';
import { Icon } from '../../../shared/components/icon';
import { MarkdownPipe } from '../../../shared/pipes/markdown.pipe';
import { DateTimePipe, Percent100Pipe } from '../../../shared/pipes/format.pipes';
import { JOB_STATUS } from '../jobs/jobs-page';

export const METRICS: { key: keyof EvalMetrics; label: string; hint: string; group: 'retrieval' | 'generation' }[] = [
  { key: 'hit_rate', label: 'Hit rate', hint: 'Fração de perguntas em que algum documento esperado foi recuperado.', group: 'retrieval' },
  { key: 'mrr', label: 'MRR', hint: 'Média do inverso da posição do primeiro documento esperado.', group: 'retrieval' },
  { key: 'recall', label: 'Recall', hint: 'Fração dos documentos esperados presentes no contexto.', group: 'retrieval' },
  { key: 'context_precision', label: 'Precisão do contexto', hint: 'Fração dos trechos do contexto que vêm de documentos esperados.', group: 'retrieval' },
  { key: 'faithfulness', label: 'Fidelidade', hint: 'A resposta é sustentada pelo contexto? (LLM como juiz)', group: 'generation' },
  { key: 'answer_relevance', label: 'Relevância', hint: 'A resposta atende à pergunta? (LLM como juiz)', group: 'generation' },
  { key: 'correctness', label: 'Correção', hint: 'A resposta concorda com a referência? (LLM como juiz)', group: 'generation' },
];

interface CaseForm {
  id: string | null;
  question: string;
  expected_answer: string;
  expected_documents: string[];
  tags: string;
}

@Component({
  selector: 'app-evals-page',
  imports: [FormsModule, Icon, DateTimePipe, Percent100Pipe, MarkdownPipe],
  templateUrl: './evals-page.html',
  styleUrl: './evals-page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EvalsPage implements OnInit {
  private readonly api = inject(AdminApi);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);

  protected readonly tab = signal<'runs' | 'cases'>('runs');
  protected readonly cases = signal<EvalCase[]>([]);
  protected readonly runs = signal<EvalRun[]>([]);
  protected readonly run = signal<EvalRunDetail | null>(null);
  protected readonly documentNames = signal<string[]>([]);
  protected readonly selectedCases = signal<Set<string>>(new Set());
  protected readonly expandedResult = signal<string | null>(null);
  protected readonly loading = signal(true);

  protected readonly caseForm = signal<CaseForm | null>(null);
  protected readonly runDialog = signal(false);
  protected readonly generateDialog = signal(false);
  protected runName = '';
  protected generateCount = 10;
  protected docToAdd = '';

  protected readonly metrics = METRICS;
  protected readonly statusInfo = JOB_STATUS;

  protected readonly hasActiveRuns = computed(() => this.runs().some((r) => r.status === 'queued' || r.status === 'running'));

  constructor() {
    const timer = setInterval(() => {
      if (this.hasActiveRuns()) this.refreshRuns();
      const current = this.run();
      if (current && (current.status === 'queued' || current.status === 'running')) this.openRun(current.id, false);
    }, 4000);
    inject(DestroyRef).onDestroy(() => clearInterval(timer));
  }

  async ngOnInit(): Promise<void> {
    await Promise.all([this.refreshRuns(), this.refreshCases()]);
    this.loading.set(false);
    this.api.documentNames().then((names) => this.documentNames.set(names)).catch(() => undefined);
  }

  async refreshRuns(): Promise<void> {
    try {
      this.runs.set(await this.api.evalRuns());
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  async refreshCases(): Promise<void> {
    try {
      this.cases.set(await this.api.evalCases());
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  // Execuções
  protected async openRun(id: string, scroll = true): Promise<void> {
    try {
      this.run.set(await this.api.evalRun(id));
      if (scroll) window.scrollTo({ top: 0 });
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected async startRun(): Promise<void> {
    const selected = [...this.selectedCases()];
    try {
      const run = await this.api.startEvalRun(this.runName.trim() || undefined, selected.length ? selected : undefined);
      this.runDialog.set(false);
      this.runName = '';
      this.tab.set('runs');
      this.toast.success('Avaliação iniciada. Acompanhe o progresso aqui ou em Jobs.');
      await this.refreshRuns();
      this.openRun(run.id);
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected async deleteRun(run: EvalRun, event: Event): Promise<void> {
    event.stopPropagation();
    const ok = await this.confirm.ask({
      title: 'Excluir execução',
      message: `A execução "${run.name}" e seus resultados serão excluídos.`,
      confirmText: 'Excluir',
      danger: true,
    });
    if (!ok) return;
    try {
      await this.api.deleteEvalRun(run.id);
      if (this.run()?.id === run.id) this.run.set(null);
      this.refreshRuns();
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected toggleResult(result: EvalResult): void {
    this.expandedResult.update((current) => (current === result.id ? null : result.id));
  }

  protected tone(value: number | null | undefined): string {
    if (value == null) return '';
    return value >= 0.8 ? 'good' : value >= 0.5 ? 'mid' : 'bad';
  }

  protected metricValue(metrics: EvalMetrics, key: keyof EvalMetrics): number | null {
    const value = metrics[key];
    return typeof value === 'number' ? value : null;
  }

  // Casos de teste
  protected newCase(): void {
    this.caseForm.set({ id: null, question: '', expected_answer: '', expected_documents: [], tags: '' });
  }

  protected editCase(item: EvalCase): void {
    this.caseForm.set({
      id: item.id,
      question: item.question,
      expected_answer: item.expected_answer ?? '',
      expected_documents: [...item.expected_documents],
      tags: item.tags.join(', '),
    });
  }

  protected addDocument(form: CaseForm): void {
    const name = this.docToAdd.trim();
    if (name && !form.expected_documents.includes(name)) form.expected_documents.push(name);
    this.docToAdd = '';
  }

  protected removeDocument(form: CaseForm, name: string): void {
    form.expected_documents = form.expected_documents.filter((doc) => doc !== name);
  }

  protected async saveCase(form: CaseForm): Promise<void> {
    const payload: EvalCaseInput = {
      question: form.question.trim(),
      expected_answer: form.expected_answer.trim() || null,
      expected_documents: form.expected_documents,
      tags: form.tags.split(',').map((tag) => tag.trim()).filter(Boolean),
    };
    if (payload.question.length < 3) {
      this.toast.error('Informe a pergunta.');
      return;
    }
    try {
      if (form.id) await this.api.updateEvalCase(form.id, payload);
      else await this.api.createEvalCase(payload);
      this.caseForm.set(null);
      this.refreshCases();
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected async deleteCase(item: EvalCase): Promise<void> {
    const ok = await this.confirm.ask({
      title: 'Excluir caso de teste',
      message: item.question,
      confirmText: 'Excluir',
      danger: true,
    });
    if (!ok) return;
    try {
      await this.api.deleteEvalCase(item.id);
      this.selectedCases.update((set) => {
        set.delete(item.id);
        return new Set(set);
      });
      this.refreshCases();
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected toggleCase(id: string): void {
    this.selectedCases.update((set) => {
      const next = new Set(set);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  protected toggleAll(): void {
    const all = this.cases().map((c) => c.id);
    this.selectedCases.set(this.selectedCases().size === all.length ? new Set() : new Set(all));
  }

  protected async generate(): Promise<void> {
    try {
      await this.api.generateEvalCases(this.generateCount);
      this.generateDialog.set(false);
      this.toast.success('Geração de casos agendada. Eles aparecerão aqui ao final do job.');
      setTimeout(() => this.refreshCases(), 8000);
    } catch (error) {
      this.toast.error(apiErrorMessage(error));
    }
  }

  protected async importFile(input: HTMLInputElement): Promise<void> {
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text());
      const items: EvalCaseInput[] = (Array.isArray(parsed) ? parsed : parsed.cases ?? []).map((item: Partial<EvalCaseInput>) => ({
        question: String(item.question ?? ''),
        expected_answer: item.expected_answer ?? null,
        expected_documents: item.expected_documents ?? [],
        tags: item.tags ?? [],
      }));
      const result = await this.api.importEvalCases(items);
      this.toast.success(`${result.imported} casos importados.`);
      this.refreshCases();
    } catch (error) {
      this.toast.error(apiErrorMessage(error, 'Arquivo JSON inválido.'));
    }
  }

  protected exportCases(): void {
    const data = this.cases().map(({ question, expected_answer, expected_documents, tags }) => ({
      question,
      expected_answer,
      expected_documents,
      tags,
    }));
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'casos-de-teste-mon.json';
    anchor.click();
    URL.revokeObjectURL(url);
  }
}
