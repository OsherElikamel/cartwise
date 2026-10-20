import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthLayout from '../components/layout/AuthLayout';
import Button from '../components/ui/Button';
import TextField from '../components/ui/TextField';
import { useAuth } from '../contexts/AuthContext';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { getErrorMessage } from '../utils/errors';

export default function RegisterPage() {
  useDocumentTitle('Create account');
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
      setError(getErrorMessage(err, 'Could not create the account.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Pick your own branches, save your weekly list, and let CartWise learn your products."
      footer={<>Already have an account? <Link to="/login" className="font-semibold text-accent hover:underline">Sign in</Link></>}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <TextField id="name" label="Name" autoComplete="name" required minLength={2} maxLength={100} value={name} onChange={(e) => setName(e.target.value)} />
        <TextField id="email" label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <TextField
          id="password" label="Password" type="password" autoComplete="new-password" required minLength={8} maxLength={128}
          hint="At least 8 characters, with a letter and a digit."
          value={password} onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p role="alert" className="text-sm text-danger">{error}</p>}
        <Button type="submit" loading={loading} className="w-full">Create account</Button>
      </form>
    </AuthLayout>
  );
}
