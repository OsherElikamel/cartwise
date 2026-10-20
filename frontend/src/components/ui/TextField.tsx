import { Eye, EyeOff } from 'lucide-react';
import { useState, type InputHTMLAttributes } from 'react';
import { useI18n } from '../../i18n/LanguageContext';

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
}

export default function TextField({ label, hint, id, type = 'text', ...rest }: TextFieldProps) {
  const { t } = useI18n();
  const [visible, setVisible] = useState(false);
  const isPassword = type === 'password';
  return (
    <div>
      <label htmlFor={id} className="text-sm font-medium">{label}</label>
      <div className="relative mt-1">
        <input
          id={id}
          type={isPassword && visible ? 'text' : type}
          className="h-11 w-full rounded-xl border border-app-border bg-app-bg/60 px-3 pe-11 text-sm"
          {...rest}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? t('auth.hidePassword') : t('auth.showPassword')}
            className="absolute inset-y-0 end-0 flex w-11 items-center justify-center text-app-text-secondary hover:text-app-text"
          >
            {visible ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
      {hint && <p className="mt-1 text-xs text-app-text-secondary">{hint}</p>}
    </div>
  );
}
