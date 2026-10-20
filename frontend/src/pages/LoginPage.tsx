import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import AuthLayout from '../components/layout/AuthLayout';
import Button from '../components/ui/Button';
import TextField from '../components/ui/TextField';
import { useAuth } from '../contexts/AuthContext';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { RETURN_TO_KEY } from '../services/api';
import { getErrorMessage } from '../utils/errors';

export default function LoginPage() {
  useDocumentTitle('Sign in');
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      const returnTo = sessionStorage.getItem(RETURN_TO_KEY);
      sessionStorage.removeItem(RETURN_TO_KEY);
      navigate(returnTo ?? '/', { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, 'Could not sign in.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to compare at your own branches and keep your product choices."
      footer={<>New here? <Link to="/register" className="font-semibold text-accent hover:underline">Create an account</Link></>}
    >
      {params.get('expired') && (
        <p role="status" className="mb-4 rounded-xl bg-warning/10 px-3 py-2 text-sm text-warning">Your session expired. Sign in to continue where you were.</p>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <TextField id="email" label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <TextField id="password" label="Password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p role="alert" className="text-sm text-danger">{error}</p>}
        <Button type="submit" loading={loading} className="w-full">Sign in</Button>
      </form>
    </AuthLayout>
  );
}
