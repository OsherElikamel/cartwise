import type { ReactNode } from 'react';

export default function EmptyState({ icon, title, children }: { icon: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-app-border px-6 py-12 text-center">
      <div className="text-app-text-secondary opacity-60">{icon}</div>
      <p className="font-semibold">{title}</p>
      {children && <div className="max-w-sm text-sm text-app-text-secondary">{children}</div>}
    </div>
  );
}
