import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: 'sm' | 'md';
  loading?: boolean;
  icon?: ReactNode;
}

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-accent text-on-accent hover:bg-accent-hover',
  secondary: 'border border-app-border bg-app-surface text-app-text hover:bg-app-hover',
  ghost: 'text-app-text-secondary hover:bg-app-hover hover:text-app-text',
  danger: 'border border-danger/40 text-danger hover:bg-danger/10',
};

export default function Button({
  variant = 'primary', size = 'md', loading = false, icon, children, className = '', disabled, ...rest
}: ButtonProps) {
  const sizing = size === 'sm' ? 'h-9 px-3 text-sm gap-1.5' : 'h-11 px-4 text-sm gap-2';
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center rounded-xl font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${sizing} ${VARIANTS[variant]} ${className}`}
    >
      {loading ? <Loader2 size={16} className="animate-spin" aria-hidden /> : icon}
      {children}
    </button>
  );
}
