import { MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Store } from '../../types';

interface BranchContextProps {
  signedIn: boolean;
  myStores: Store[];
  demoStores: Store[];
}

/** Which branches the comparison will use, and how to change them. */
export default function BranchContext({ signedIn, myStores, demoStores }: BranchContextProps) {
  const usingDemo = myStores.length === 0;
  const stores = usingDemo ? demoStores : myStores;

  return (
    <div className="flex flex-col gap-2 rounded-2xl bg-app-elevated px-4 py-3 text-sm sm:flex-row sm:items-center">
      <MapPin size={16} className="hidden shrink-0 text-app-text-secondary sm:block" aria-hidden />
      <p className="min-w-0 flex-1 text-app-text-secondary">
        {usingDemo ? 'Comparing on the demo branches in Ashdod: ' : 'Comparing at your branches: '}
        <span className="text-app-text">{stores.map((s) => s.chain_name).join(', ') || '…'}</span>
      </p>
      {signedIn ? (
        <Link to="/branches" className="shrink-0 font-semibold text-accent hover:underline">
          {usingDemo ? 'Choose your branches' : 'Change'}
        </Link>
      ) : (
        <Link to="/register" className="shrink-0 font-semibold text-accent hover:underline">
          Sign up to use your own branches
        </Link>
      )}
    </div>
  );
}
