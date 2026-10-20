import { Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

const PHRASES = [
  'Reading your list…',
  'Checking the shelves at Rami Levy…',
  'Comparing milk prices at Shufersal…',
  'Looking for this week\'s deals…',
  'Asking Yohananof and Osher Ad…',
  'Lining up the receipts…',
];

export default function ComparingIndicator() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setIndex((i) => (i + 1) % PHRASES.length), 2200);
    return () => clearInterval(timer);
  }, []);

  return (
    <div role="status" className="flex items-center gap-3 rounded-2xl border border-app-border bg-app-surface p-5">
      <Loader2 size={18} className="animate-spin text-accent" aria-hidden />
      <span className="text-sm text-app-text-secondary">{PHRASES[index]}</span>
    </div>
  );
}
