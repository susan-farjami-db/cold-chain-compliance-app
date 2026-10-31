import type { BootstrapData, ComplianceRow } from './types';

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || body.error || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function loadData(): Promise<BootstrapData> {
  return handle<BootstrapData>(await fetch('/api/data'));
}

export async function saveData(
  rows: ComplianceRow[]
): Promise<{ saved: boolean; changed: number; user: string; rows: ComplianceRow[] }> {
  const res = await fetch('/api/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rows }),
  });
  return handle(res);
}
