import type { ReactNode } from 'react';

type Tone = 'deal' | 'warning' | 'success' | 'neutral';

const TONES: Record<Tone, string> = {
  deal: 'bg-deal text-on-deal',
  warning: 'bg-warning/15 text-warning',
  success: 'bg-success/15 text-success',
  neutral: 'bg-app-elevated text-app-text-secondary',
};

export default function Badge({ tone, icon, children, title }: { tone: Tone; icon?: ReactNode; children: ReactNode; title?: string }) {
  return (
    <span title={title} className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${TONES[tone]}`}>
      {icon}
      {children}
    </span>
  );
}
