import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthLayout from '../components/layout/AuthLayout';
import Button from '../components/ui/Button';
import TextField from '../components/ui/TextField';
import { useAuth } from '../contexts/AuthContext';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useI18n } from '../i18n/LanguageContext';
import { getErrorMessage } from '../utils/errors';

export default function RegisterPage() {
  const { t } = useI18n();
  useDocumentTitle(t('title.register'));
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register(name, email, password);
      navigate('/branches', { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, t, 'auth.createFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title={t('auth.createTitle')}
      subtitle={t('auth.createSubtitle')}
      footer={<>{t('auth.haveAccount')} <Link to="/login" className="font-semibold text-accent hover:underline">{t('auth.signIn')}</Link></>}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <TextField id="name" label={t('auth.name')} autoComplete="name" required minLength={2} maxLength={100} value={name} onChange={(e) => setName(e.target.value)} />
        <TextField id="email" label={t('auth.email')} type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <TextField
          id="password" label={t('auth.password')} type="password" autoComplete="new-password" required minLength={8} maxLength={128}
          hint={t('auth.passwordHint')}
          value={password} onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p role="alert" className="text-sm text-danger">{error}</p>}
        <Button type="submit" loading={loading} className="w-full">{t('auth.createButton')}</Button>
      </form>
    </AuthLayout>
  );
}
