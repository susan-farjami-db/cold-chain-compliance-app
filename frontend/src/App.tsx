import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Snowflake,
  Plus,
  Trash2,
  Save,
  RotateCw,
  Loader2,
  Truck,
  CheckCircle2,
  AlertTriangle,
  CircleUser,
} from 'lucide-react';
import { loadData, saveData } from './api';
import type { ComplianceRow } from './types';
import { TVAL_COMPLIANT } from './types';
import { StatCard } from './components/StatCard';
import { DataTable } from './components/DataTable';

function uid() {
  return (
    (crypto.randomUUID && crypto.randomUUID()) ||
    'row-' + Math.random().toString(36).slice(2) + Date.now().toString(36)
  );
}

function blankRow(): ComplianceRow {
  return {
    row_id: uid(),
    unit_number: '',
    trailer_type: '',
    owner_name: '',
    last_update_date: '',
    last_change_description: '',
    updated_by: '',
    pending_action_items: '',
    tval_status: '',
    recert_appt_date: '',
  };
}

type Toast = { kind: 'success' | 'error'; msg: string } | null;

export default function App() {
  const [rows, setRows] = useState<ComplianceRow[]>([]);
  const [units, setUnits] = useState<string[]>([]);
  const [tvalStatuses, setTvalStatuses] = useState<string[]>([]);
  const [user, setUser] = useState<string>('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<Toast>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setToast(null);
    try {
      const data = await loadData();
      setRows(data.rows.map((r) => ({ ...r, row_id: uid() })));
      setUnits(data.units);
      setTvalStatuses(data.tval_statuses);
      setUser(data.user);
      setSelected(new Set());
    } catch (e) {
      setToast({ kind: 'error', msg: `Could not load data: ${(e as Error).message}` });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const stats = useMemo(() => {
    const tracked = rows.filter((r) => r.unit_number.trim()).length;
    const compliant = rows.filter((r) => r.tval_status === TVAL_COMPLIANT).length;
    return { tracked, compliant, pending: tracked - compliant };
  }, [rows]);

  const onChange = useCallback(
    (id: string, field: keyof ComplianceRow, value: string) => {
      setRows((prev) =>
        prev.map((r) => (r.row_id === id ? { ...r, [field]: value } : r))
      );
    },
    []
  );

  const addRow = () => setRows((prev) => [blankRow(), ...prev]);

  const deleteSelected = () => {
    if (selected.size === 0) return;
    setRows((prev) => prev.filter((r) => !selected.has(r.row_id)));
    setSelected(new Set());
  };

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const toggleAll = (checked: boolean) =>
    setSelected(checked ? new Set(rows.map((r) => r.row_id)) : new Set());

  const save = async () => {
    setSaving(true);
    setToast(null);
    try {
      const res = await saveData(rows);
      setRows(res.rows.map((r) => ({ ...r, row_id: uid() })));
      setSelected(new Set());
      setToast({
        kind: 'success',
        msg: `Saved. ${res.changed} row(s) stamped with today's date and your name (${res.user}).`,
      });
    } catch (e) {
      setToast({ kind: 'error', msg: `Save failed: ${(e as Error).message}` });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-[1320px] px-6 py-8">
      {/* Header */}
      <header className="mb-7 flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-sky-400 text-white shadow-soft">
            <Snowflake className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">
              Cold Chain — T-Val Compliance
            </h1>
            <p className="mt-0.5 text-sm text-slate-500">
              Fleet temperature-validation compliance
            </p>
          </div>
        </div>
        {user && (
          <div className="flex items-center gap-2 rounded-full bg-white px-3.5 py-1.5 text-sm font-medium text-slate-600 shadow-card ring-1 ring-slate-200">
            <CircleUser className="h-4 w-4 text-brand-600" />
            {user}
          </div>
        )}
      </header>

      {/* Stat cards */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Units tracked"
          value={stats.tracked}
          accent="blue"
          icon={<Truck className="h-6 w-6" />}
        />
        <StatCard
          label="Compliant for T-Val"
          value={stats.compliant}
          accent="green"
          icon={<CheckCircle2 className="h-6 w-6" />}
        />
        <StatCard
          label="Pending HQ approval"
          value={stats.pending}
          accent="red"
          icon={<AlertTriangle className="h-6 w-6" />}
        />
      </div>

      {/* Toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-2.5">
        <button
          onClick={addRow}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 shadow-card transition hover:bg-slate-50 active:scale-[.98]"
        >
          <Plus className="h-4 w-4" /> Add unit
        </button>
        <button
          onClick={deleteSelected}
          disabled={selected.size === 0}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 shadow-card transition hover:bg-slate-50 active:scale-[.98] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Trash2 className="h-4 w-4" /> Delete selected
          {selected.size > 0 && (
            <span className="ml-0.5 rounded-full bg-slate-200 px-1.5 text-xs">
              {selected.size}
            </span>
          )}
        </button>
        <div className="flex-1" />
        <button
          onClick={refresh}
          disabled={loading || saving}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-semibold text-slate-600 shadow-card transition hover:bg-slate-50 active:scale-[.98] disabled:opacity-50"
        >
          <RotateCw className={'h-4 w-4 ' + (loading ? 'animate-spin' : '')} /> Refresh
        </button>
        <button
          onClick={save}
          disabled={saving || loading}
          className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-700 active:scale-[.98] disabled:opacity-60"
        >
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>

      {/* Toast */}
      {toast && (
        <div
          className={
            'mb-4 flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium ring-1 ' +
            (toast.kind === 'success'
              ? 'bg-emerald-50 text-emerald-800 ring-emerald-200'
              : 'bg-red-50 text-red-800 ring-red-200')
          }
        >
          {toast.kind === 'success' ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <AlertTriangle className="h-4 w-4" />
          )}
          {toast.msg}
        </div>
      )}

      {/* Table (with loading overlay) */}
      <div className="relative">
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-2xl bg-white/70 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
              <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
              Loading fleet data…
            </div>
          </div>
        )}
        <DataTable
          rows={rows}
          units={units}
          tvalStatuses={tvalStatuses}
          selected={selected}
          onToggle={toggle}
          onToggleAll={toggleAll}
          onChange={onChange}
        />
      </div>

      <footer className="mt-6 text-center text-xs text-slate-400">
        Last Updated &amp; Updated By are stamped automatically on save. Blank Unit # rows are
        ignored.
      </footer>
    </div>
  );
}
