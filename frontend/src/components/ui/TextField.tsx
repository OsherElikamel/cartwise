import { Eye, EyeOff } from 'lucide-react';
import { useState, type InputHTMLAttributes } from 'react';

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
}

export default function TextField({ label, hint, id, type = 'text', ...rest }: TextFieldProps) {
  const [visible, setVisible] = useState(false);
  const isPassword = type === 'password';
  return (
    <div>
      <label htmlFor={id} className="text-sm font-medium">{label}</label>
      <div className="relative mt-1">
        <input
          id={id}
          type={isPassword && visible ? 'text' : type}
          className="h-11 w-full rounded-xl border border-app-border bg-app-bg px-3 pr-11 text-sm"
          {...rest}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? 'Hide password' : 'Show password'}
            className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-app-text-secondary hover:text-app-text"
          >
            {visible ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
      {hint && <p className="mt-1 text-xs text-app-text-secondary">{hint}</p>}
    </div>
  );
}
