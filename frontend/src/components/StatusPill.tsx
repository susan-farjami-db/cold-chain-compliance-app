import { CheckCircle2, AlertTriangle, Circle } from 'lucide-react';
import { TVAL_COMPLIANT } from '../types';

export function StatusPill({ status }: { status: string }) {
  if (!status) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500">
        <Circle className="h-3 w-3" />
        Unset
      </span>
    );
  }
  const compliant = status === TVAL_COMPLIANT;
  return (
    <span
      className={
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ' +
        (compliant
          ? 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200'
          : 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-200')
      }
    >
      {compliant ? (
        <CheckCircle2 className="h-3.5 w-3.5" />
      ) : (
        <AlertTriangle className="h-3.5 w-3.5" />
      )}
      {compliant ? 'Compliant' : 'Pending HQ'}
    </span>
  );
}
