import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { apiErrorMessage } from './api-error';
import { ToastService } from './toast.service';

/** Baixa o arquivo original de um documento (requisição autenticada). */
@Injectable({ providedIn: 'root' })
export class DownloadService {
  private readonly http = inject(HttpClient);
  private readonly toast = inject(ToastService);

  async document(documentId: string, filename: string): Promise<void> {
    try {
      const blob = await firstValueFrom(
        this.http.get(`/api/documents/${documentId}/download`, { responseType: 'blob' }),
      );
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = filename;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 10_000);
    } catch (error) {
      this.toast.error(apiErrorMessage(error, 'Não foi possível baixar o arquivo.'));
    }
  }
}
