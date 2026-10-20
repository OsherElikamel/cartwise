import { Link } from 'react-router-dom';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useI18n } from '../i18n/LanguageContext';

export default function NotFoundPage() {
  const { t } = useI18n();
  useDocumentTitle(t('title.notFound'));
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <p className="font-mono text-4xl font-bold">404</p>
      <p className="text-app-text-secondary">{t('notFound.body')}</p>
      <Link to="/" className="font-semibold text-accent hover:underline">{t('notFound.back')}</Link>
    </div>
  );
}
