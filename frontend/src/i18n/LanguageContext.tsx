import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import en, { type MessageKey } from './en';
import he from './he';

export type Lang = 'en' | 'he';

const LANG_KEY = 'cartwise_lang';
const MESSAGES: Record<Lang, Record<MessageKey, string>> = { en, he };
const LOCALES: Record<Lang, string> = { en: 'en-IL', he: 'he-IL' };

// The four chains are fixed by the backend's chain registry. Keyed by slug,
// with the English name as an alias (history rows store the English name).
const CHAINS: Record<string, { en: string; he: string }> = {
  shufersal: { en: 'Shufersal', he: 'שופרסל' },
  'rami-levy': { en: 'Rami Levy', he: 'רמי לוי' },
  yohananof: { en: 'Yohananof', he: 'יוחננוף' },
  'osher-ad': { en: 'Osher Ad', he: 'אושר עד' },
};
const CHAIN_BY_NAME = Object.fromEntries(
  Object.entries(CHAINS).flatMap(([slug, names]) => [[slug, names], [names.en, names]]),
);

type Vars = Record<string, string | number>;

interface LanguageState {
  lang: Lang;
  dir: 'ltr' | 'rtl';
  toggleLanguage: () => void;
  t: (key: MessageKey, vars?: Vars) => string;
  /** Plural: picks `${base}_one` or `${base}_other` and fills {count}. */
  tp: (base: string, count: number, vars?: Vars) => string;
  price: (value: string | number) => string;
  date: (iso: string) => string;
  dateTime: (iso: string) => string;
  quantity: (quantity: number, unit: 'unit' | 'kg') => string;
  /** Chain display name in the current language, from its English name or slug. */
  chain: (nameOrSlug: string) => string;
}

function initialLang(): Lang {
  const stored = localStorage.getItem(LANG_KEY);
  if (stored === 'en' || stored === 'he') return stored;
  return navigator.language.toLowerCase().startsWith('he') ? 'he' : 'en';
}

function fill(template: string, vars?: Vars): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) => (name in vars ? String(vars[name]) : match));
}

const LanguageContext = createContext<LanguageState | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(initialLang);
  const dir = lang === 'he' ? 'rtl' : 'ltr';

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
    localStorage.setItem(LANG_KEY, lang);
  }, [lang, dir]);

  const t = useCallback((key: MessageKey, vars?: Vars) => fill(MESSAGES[lang][key], vars), [lang]);

  const value = useMemo<LanguageState>(() => {
    const locale = LOCALES[lang];
    const money = new Intl.NumberFormat(locale, { style: 'currency', currency: 'ILS', minimumFractionDigits: 2 });
    return {
      lang,
      dir,
      toggleLanguage: () => setLang((l) => (l === 'en' ? 'he' : 'en')),
      t,
      tp: (base, count, vars) => t(`${base}_${count === 1 ? 'one' : 'other'}` as MessageKey, { count, ...vars }),
      price: (v) => money.format(typeof v === 'string' ? Number(v) : v),
      date: (iso) => new Date(iso).toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' }),
      dateTime: (iso) => new Date(iso).toLocaleString(locale, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }),
      quantity: (q, unit) => {
        const n = Number.isInteger(q) ? String(q) : q.toFixed(2).replace(/0+$/, '');
        return unit === 'kg' ? `${n} ${t('line.kg')}` : `${n} ×`;
      },
      chain: (name) => CHAIN_BY_NAME[name]?.[lang] ?? name,
    };
  }, [lang, dir, t]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useI18n() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useI18n must be used within LanguageProvider');
  return ctx;
}
