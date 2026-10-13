import { HttpErrorResponse } from '@angular/common/http';

/** Extrai a mensagem amigável de um erro da API. */
export function apiErrorMessage(error: unknown, fallback = 'Algo deu errado. Tente novamente.'): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) return 'Não foi possível conectar ao servidor.';
    const detail = error.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}
