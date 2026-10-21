import { useEffect, useRef, type ReactNode } from 'react';

interface DialogProps {
  title: string;
  children: ReactNode;
  actions: ReactNode;
  onClose: () => void;
}

/** A small modal: focus moves into it, Escape and the backdrop close it. */
export default function Dialog({ title, children, actions, onClose }: DialogProps) {
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    panel.current?.querySelector<HTMLElement>('button')?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-[90] flex items-end justify-center bg-black/50 p-4 sm:items-center" onClick={onClose}>
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        onClick={(e) => e.stopPropagation()}
        className="animate-fade-in w-full max-w-md rounded-3xl border border-app-border bg-app-surface p-6 shadow-2xl"
      >
        <h2 id="dialog-title" className="text-xl font-bold">{title}</h2>
        <div className="mt-2 text-sm text-app-text-secondary">{children}</div>
        <div className="mt-5 flex flex-col gap-2">{actions}</div>
      </div>
    </div>
  );
}
