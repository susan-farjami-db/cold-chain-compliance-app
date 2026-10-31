import type { ReactNode } from 'react';

interface Props {
  label: string;
  value: number;
  icon: ReactNode;
  accent: 'blue' | 'green' | 'red';
}

const ACCENTS = {
  blue: { ring: 'ring-brand-100', icon: 'bg-brand-50 text-brand-600', value: 'text-brand-700' },
  green: { ring: 'ring-emerald-100', icon: 'bg-emerald-50 text-emerald-600', value: 'text-emerald-700' },
  red: { ring: 'ring-red-100', icon: 'bg-red-50 text-red-600', value: 'text-red-700' },
};

export function StatCard({ label, value, icon, accent }: Props) {
  const a = ACCENTS[accent];
  return (
    <div
      className={`flex items-center gap-4 rounded-2xl bg-white p-5 shadow-card ring-1 ${a.ring}`}
    >
      <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${a.icon}`}>
        {icon}
      </div>
      <div>
        <div className={`text-3xl font-extrabold tracking-tight ${a.value}`}>{value}</div>
        <div className="text-sm font-medium text-slate-500">{label}</div>
      </div>
    </div>
  );
}
