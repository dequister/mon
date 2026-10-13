// Contratos da API (espelham os schemas do backend).

export type Role = 'admin' | 'user';

export interface User {
  id: string;
  username: string;
  full_name: string;
  role: Role;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Source {
  index: number;
  document_id: string;
  filename: string;
  file_type: string;
  page: number | null;
  sheet: string | null;
  heading: string | null;
  chunk_index: number;
  ocr: boolean;
  source: string;
  indexed_at: string | null;
  vector_score: number;
  rerank_score: number | null;
  snippet: string;
  cited: boolean;
}

export interface MessageDetails {
  provider?: string;
  model?: string;
  search_query?: string;
  candidates?: number;
  latency_ms?: number;
  timings_ms?: Record<string, number>;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: Source[];
  details: MessageDetails;
  error: string | null;
  created_at: string;
}

export type DocumentStatus = 'pending' | 'processing' | 'indexed' | 'failed';

export interface PageReport {
  page: number;
  ocr: boolean;
  reason: string;
  text_chars: number;
  image_coverage: number;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  mime_type: string | null;
  size_bytes: number;
  sha256: string;
  source: 'upload' | 'folder';
  source_path: string | null;
  status: DocumentStatus;
  version: number;
  chunk_count: number;
  page_count: number | null;
  ocr_pages: number;
  extraction: { sections?: number; characters?: number; title?: string; pages?: PageReport[]; sheets?: string[] };
  error: string | null;
  created_at: string;
  updated_at: string;
  indexed_at: string | null;
}

export interface UploadItem {
  filename: string;
  status: 'created' | 'updated' | 'duplicate' | 'rejected';
  message: string;
  document: DocumentItem | null;
  job_id: string | null;
}

export interface DocumentStats {
  total: number;
  by_status: Partial<Record<DocumentStatus, number>>;
  chunks: number;
  vectors: number | null;
  supported_extensions: string[];
}

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'canceled';
export type JobType = 'ingest_document' | 'sync_folder' | 'reindex_all' | 'eval_run' | 'eval_generate';

export interface Job {
  id: string;
  type: JobType;
  status: JobStatus;
  priority: number;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  progress: number;
  message: string | null;
  error: string | null;
  attempts: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface JobDetail extends Job {
  log: string;
}

export type ReasoningLevel = 'low' | 'medium' | 'high';

export interface RagSettings {
  llm_provider: string;
  llm_model: string;
  reasoning_level: ReasoningLevel;
  system_prompt: string;
  retrieval_top_k: number;
  rerank_enabled: boolean;
  rerank_model: string;
  rerank_top_n: number;
  min_relevance: number;
  query_rewrite_enabled: boolean;
  history_window: number;
  chunk_size: number;
  chunk_overlap: number;
}

export interface Provider {
  id: string;
  name: string;
  configured: boolean;
}

export interface ModelInfo {
  id: string;
  provider: string;
  display_name: string;
  description: string;
  input_token_limit: number | null;
  output_token_limit: number | null;
  supports_thinking: boolean | null;
  created: number | null;
}

export interface ModelTestResult {
  ok: boolean;
  latency_ms: number | null;
  reply: string | null;
  error: string | null;
}

export interface EvalCase {
  id: string;
  question: string;
  expected_answer: string | null;
  expected_documents: string[];
  tags: string[];
  created_at: string;
}

export type EvalCaseInput = Omit<EvalCase, 'id' | 'created_at'>;

export interface EvalMetrics {
  cases?: number;
  errors?: number;
  hit_rate?: number | null;
  mrr?: number | null;
  recall?: number | null;
  context_precision?: number | null;
  faithfulness?: number | null;
  answer_relevance?: number | null;
  correctness?: number | null;
  latency_ms_avg?: number | null;
  latency_ms_p95?: number | null;
}

export interface EvalRun {
  id: string;
  name: string;
  status: JobStatus;
  config: Record<string, unknown> & { llm_model?: string; llm_provider?: string; rerank_model?: string };
  metrics: EvalMetrics;
  case_count: number;
  job_id: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface EvalResult {
  id: string;
  case_id: string | null;
  position: number;
  question: string;
  expected_answer: string | null;
  expected_documents: string[];
  answer: string;
  retrieved: { index: number; filename: string; page: number | null; sheet: string | null; rerank_score: number | null; vector_score: number; cited: boolean }[];
  metrics: EvalMetrics;
  judge_reason: string | null;
  latency_ms: number;
  error: string | null;
}

export interface EvalRunDetail extends EvalRun {
  results: EvalResult[];
}
