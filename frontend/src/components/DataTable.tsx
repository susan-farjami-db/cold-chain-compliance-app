import type { ComplianceRow } from '../types';
import { StatusPill } from './StatusPill';
import { Lock } from 'lucide-react';

interface Props {
  rows: ComplianceRow[];
  units: string[];
  tvalStatuses: string[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  onToggleAll: (checked: boolean) => void;
  onChange: (id: string, field: keyof ComplianceRow, value: string) => void;
}

const inputCls =
  'w-full rounded-md border border-transparent bg-transparent px-2 py-1.5 text-sm text-slate-700 outline-none transition hover:border-slate-200 focus:border-brand-600 focus:bg-white focus:ring-2 focus:ring-brand-100';

export function DataTable({
  rows,
  units,
  tvalStatuses,
  selected,
  onToggle,
  onToggleAll,
  onChange,
}: Props) {
  const allSelected = rows.length > 0 && rows.every((r) => selected.has(r.row_id));

  return (
    <div className="overflow-hidden rounded-2xl bg-white shadow-soft ring-1 ring-slate-200">
      <div className="tbl-scroll overflow-x-auto">
        <table className="w-full min-w-[1180px] border-collapse text-left">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/80 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <th className="w-10 px-4 py-3">
                <input
                  type="checkbox"
                  className="h-4 w-4 cursor-pointer rounded border-slate-300 text-brand-600 focus:ring-brand-600"
                  checked={allSelected}
                  onChange={(e) => onToggleAll(e.target.checked)}
                />
              </th>
              <th className="px-3 py-3">Unit #</th>
              <th className="px-3 py-3">Trailer</th>
              <th className="px-3 py-3">Owner / Contractor</th>
              <th className="px-3 py-3">T-Val Status</th>
              <th className="px-3 py-3">Last Change Description</th>
              <th className="px-3 py-3">Pending Action Items</th>
              <th className="px-3 py-3">Re-Cert / Install Appt</th>
              <th className="px-3 py-3">
                <span className="inline-flex items-center gap-1">
                  <Lock className="h-3 w-3" /> Last Updated
                </span>
              </th>
              <th className="px-3 py-3">
                <span className="inline-flex items-center gap-1">
                  <Lock className="h-3 w-3" /> Updated By
                </span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.length === 0 && (
              <tr>
                <td colSpan={10} className="px-4 py-16 text-center text-sm text-slate-400">
                  No units tracked yet. Click “Add unit” to create a row.
                </td>
              </tr>
            )}
            {rows.map((r) => {
              const isSel = selected.has(r.row_id);
              return (
                <tr
                  key={r.row_id}
                  className={
                    'transition ' + (isSel ? 'bg-brand-50/50' : 'hover:bg-slate-50/60')
                  }
                >
                  <td className="px-4 py-2 align-top">
                    <input
                      type="checkbox"
                      className="mt-1.5 h-4 w-4 cursor-pointer rounded border-slate-300 text-brand-600 focus:ring-brand-600"
                      checked={isSel}
                      onChange={() => onToggle(r.row_id)}
                    />
                  </td>
                  <td className="px-3 py-2 align-top">
                    <select
                      className={inputCls + ' font-medium'}
                      value={r.unit_number}
                      onChange={(e) => onChange(r.row_id, 'unit_number', e.target.value)}
                    >
                      <option value=""></option>
                      {units.map((u) => (
                        <option key={u} value={u}>
                          {u}
                        </option>
                      ))}
                      {/* preserve a value not in the master list */}
                      {r.unit_number && !units.includes(r.unit_number) && (
                        <option value={r.unit_number}>{r.unit_number}</option>
                      )}
                    </select>
                  </td>
                  <td className="px-3 py-2 align-top">
                    <input
                      className={inputCls}
                      value={r.trailer_type}
                      onChange={(e) => onChange(r.row_id, 'trailer_type', e.target.value)}
                    />
                  </td>
                  <td className="px-3 py-2 align-top">
                    <input
                      className={inputCls}
                      value={r.owner_name}
                      onChange={(e) => onChange(r.row_id, 'owner_name', e.target.value)}
                    />
                  </td>
                  <td className="px-3 py-2 align-top">
                    <div className="flex flex-col gap-1.5">
                      <StatusPill status={r.tval_status} />
                      <select
                        className={inputCls + ' text-xs'}
                        value={r.tval_status}
                        onChange={(e) => onChange(r.row_id, 'tval_status', e.target.value)}
                      >
                        <option value=""></option>
                        {tvalStatuses.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </div>
                  </td>
                  <td className="px-3 py-2 align-top">
                    <textarea
                      rows={2}
                      className={inputCls + ' resize-y'}
                      value={r.last_change_description}
                      onChange={(e) =>
                        onChange(r.row_id, 'last_change_description', e.target.value)
                      }
                    />
                  </td>
                  <td className="px-3 py-2 align-top">
                    <textarea
                      rows={2}
                      className={inputCls + ' resize-y'}
                      value={r.pending_action_items}
                      onChange={(e) =>
                        onChange(r.row_id, 'pending_action_items', e.target.value)
                      }
                    />
                  </td>
                  <td className="px-3 py-2 align-top">
                    <input
                      className={inputCls}
                      value={r.recert_appt_date}
                      onChange={(e) => onChange(r.row_id, 'recert_appt_date', e.target.value)}
                    />
                  </td>
                  <td className="px-3 py-2 align-top">
                    <div className="px-2 py-1.5 text-sm text-slate-400">
                      {r.last_update_date || '—'}
                    </div>
                  </td>
                  <td className="px-3 py-2 align-top">
                    <div className="px-2 py-1.5 text-sm text-slate-400">
                      {r.updated_by || '—'}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
