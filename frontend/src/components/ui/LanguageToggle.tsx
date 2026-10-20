import { Languages } from 'lucide-react';
import { useI18n } from '../../i18n/LanguageContext';

/** Shows the other language's name, in that language: "עברית" while in English. */
export default function LanguageToggle() {
  const { t, toggleLanguage, lang } = useI18n();
  return (
    <button
      type="button"
      onClick={toggleLanguage}
      aria-label={t('lang.toggleAria')}
      lang={lang === 'en' ? 'he' : 'en'}
      className="flex h-10 shrink-0 items-center gap-1.5 rounded-full px-2.5 text-sm font-semibold text-app-text-secondary hover:bg-app-hover hover:text-app-text"
    >
      <Languages size={16} aria-hidden />
      <span className="hidden sm:inline">{t('lang.toggle')}</span>
      <span className="sm:hidden">{lang === 'en' ? 'עב' : 'EN'}</span>
    </button>
  );
}
