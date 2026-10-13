import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'fileSize' })
export class FileSizePipe implements PipeTransform {
  transform(bytes: number | null | undefined): string {
    if (bytes == null) return '—';
    const units = ['B', 'KB', 'MB', 'GB'];
    let value = bytes;
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
      value /= 1024;
      unit++;
    }
    return `${value.toLocaleString('pt-BR', { maximumFractionDigits: unit ? 1 : 0 })} ${units[unit]}`;
  }
}

@Pipe({ name: 'dateTime' })
export class DateTimePipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value) return '—';
    return new Date(value).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
  }
}

@Pipe({ name: 'relativeTime' })
export class RelativeTimePipe implements PipeTransform {
  private readonly format = new Intl.RelativeTimeFormat('pt-BR', { numeric: 'auto' });

  transform(value: string | null | undefined): string {
    if (!value) return '—';
    const seconds = Math.round((new Date(value).getTime() - Date.now()) / 1000);
    const steps: [Intl.RelativeTimeFormatUnit, number][] = [
      ['second', 60],
      ['minute', 60],
      ['hour', 24],
      ['day', 30],
      ['month', 12],
    ];
    let amount = seconds;
    for (const [unit, size] of steps) {
      if (Math.abs(amount) < size) return this.format.format(amount, unit);
      amount = Math.round(amount / size);
    }
    return this.format.format(amount, 'year');
  }
}

@Pipe({ name: 'duration' })
export class DurationPipe implements PipeTransform {
  transform(start: string | null | undefined, end?: string | null): string {
    if (!start) return '—';
    const ms = (end ? new Date(end).getTime() : Date.now()) - new Date(start).getTime();
    if (ms < 1000) return `${Math.max(ms, 0)} ms`;
    const seconds = Math.round(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    return `${minutes}min ${seconds % 60}s`;
  }
}

@Pipe({ name: 'percent100' })
export class Percent100Pipe implements PipeTransform {
  transform(value: number | null | undefined, digits = 0): string {
    if (value == null) return '—';
    return `${(value * 100).toLocaleString('pt-BR', { maximumFractionDigits: digits })}%`;
  }
}
