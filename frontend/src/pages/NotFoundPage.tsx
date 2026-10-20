import { Link } from 'react-router-dom';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

export default function NotFoundPage() {
  useDocumentTitle('Not found');
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <p className="font-mono text-4xl font-bold">404</p>
      <p className="text-app-text-secondary">This aisle doesn't exist.</p>
      <Link to="/" className="font-semibold text-accent hover:underline">Back to comparing</Link>
    </div>
  );
}
