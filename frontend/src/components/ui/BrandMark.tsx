import { ReceiptText } from 'lucide-react';

export default function BrandMark({ size = 'sm' }: { size?: 'sm' | 'lg' }) {
  const box = size === 'lg' ? 'h-14 w-14 rounded-2xl' : 'h-8 w-8 rounded-lg';
  return (
    <span className={`relative inline-flex items-center justify-center bg-accent text-on-accent ${box}`}>
      <ReceiptText size={size === 'lg' ? 28 : 17} aria-hidden />
      <span className="absolute -right-1 -top-1 h-3 w-3 rounded-full bg-deal ring-2 ring-app-bg" aria-hidden />
    </span>
  );
}
