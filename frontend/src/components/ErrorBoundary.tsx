import { Component, type ErrorInfo, type ReactNode } from 'react';
import en from '../i18n/en';
import he from '../i18n/he';

interface State {
  hasError: boolean;
}

/** Sits outside every provider, so it reads the language directly. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Render crash:', error, info.componentStack);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    const m = document.documentElement.lang === 'he' ? he : en;
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="text-lg font-semibold">{m['error.crashTitle']}</p>
        <p className="text-sm text-app-text-secondary">{m['error.crashBody']}</p>
        <button
          type="button"
          onClick={() => window.location.assign('/')}
          className="h-11 rounded-full bg-accent px-5 text-sm font-semibold text-on-accent"
        >
          {m['error.crashBack']}
        </button>
      </div>
    );
  }
}
