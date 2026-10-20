import { MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useI18n } from '../../i18n/LanguageContext';
import type { Store } from '../../types';

interface BranchContextProps {
  signedIn: boolean;
  myStores: Store[];
  demoStores: Store[];
}

/** Which branches the comparison will use, and how to change them. */
export default function BranchContext({ signedIn, myStores, demoStores }: BranchContextProps) {
  const { t, chain } = useI18n();
  const usingDemo = myStores.length === 0;
  const stores = usingDemo ? demoStores : myStores;

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-app-border bg-app-elevated/60 px-4 py-3 text-sm sm:flex-row sm:items-center">
      <MapPin size={16} className="hidden shrink-0 text-app-text-secondary sm:block" aria-hidden />
      <p className="min-w-0 flex-1 text-app-text-secondary">
        {usingDemo ? t('context.demo') : t('context.mine')}{' '}
        <span className="text-app-text">{stores.map((s) => chain(s.chain_slug)).join(', ') || '…'}</span>
      </p>
      <Link to={signedIn ? '/branches' : '/register'} className="shrink-0 font-semibold text-accent hover:underline">
        {signedIn ? (usingDemo ? t('context.choose') : t('context.change')) : t('context.signUp')}
      </Link>
    </div>
  );
}
