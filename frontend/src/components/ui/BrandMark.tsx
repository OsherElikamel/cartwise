import { ReceiptText } from 'lucide-react';

export default function BrandMark({ size = 'sm' }: { size?: 'sm' | 'lg' }) {
  const box = size === 'lg' ? 'h-14 w-14 rounded-2xl' : 'h-9 w-9 rounded-xl';
  return (
    <span className={`relative inline-flex items-center justify-center bg-linear-to-br from-brand-from to-brand-to text-white shadow-lg shadow-brand-from/30 ${box}`}>
      <ReceiptText size={size === 'lg' ? 28 : 18} aria-hidden />
      <span className="absolute -end-1 -top-1 h-3 w-3 rounded-full bg-deal ring-2 ring-app-bg" aria-hidden />
    </span>
  );
}
