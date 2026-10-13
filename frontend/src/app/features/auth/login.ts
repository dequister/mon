import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { apiErrorMessage } from '../../core/services/api-error';
import { AuthService } from '../../core/services/auth.service';
import { Icon } from '../../shared/components/icon';
import { MonLogo } from '../../shared/components/mon-logo';

@Component({
  selector: 'app-login',
  imports: [FormsModule, Icon, MonLogo],
  templateUrl: './login.html',
  styleUrl: './login.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginPage {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected username = '';
  protected password = '';
  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);

  async submit(): Promise<void> {
    if (!this.username || !this.password || this.loading()) return;
    this.loading.set(true);
    this.error.set(null);
    try {
      await this.auth.login(this.username, this.password);
      this.router.navigate(['/']);
    } catch (error) {
      this.error.set(apiErrorMessage(error, 'Não foi possível entrar.'));
    } finally {
      this.loading.set(false);
    }
  }
}
