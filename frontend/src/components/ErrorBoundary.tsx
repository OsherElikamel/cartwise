import { Component, type ErrorInfo, type ReactNode } from 'react';
import en from '../i18n/en';
import he from '../i18n/he';

interface State {
  hasError: boolean;
}

const RELOADED_KEY = 'cartwise_reloaded_for_update';

/** After a new deploy, a page loaded earlier asks for code files that no longer
 *  exist. That is not a bug in the page: reload once to get the new version. */
function isStaleDeploy(error: Error): boolean {
  return /dynamically imported module|Importing a module script failed|Unable to preload CSS/i.test(error.message);
}

/** Send the crash to the server log, so crashes on someone else's screen are visible. */
function report(error: Error, info: ErrorInfo) {
  const body = JSON.stringify({
    message: `${error.name}: ${error.message}`.slice(0, 500),
    stack: `${error.stack ?? ''}\n${info.componentStack ?? ''}`.slice(0, 4000),
    url: window.location.pathname.slice(0, 300),
  });
  fetch(`${import.meta.env.VITE_API_BASE_URL}/client-errors`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body, keepalive: true,
  }).catch(() => undefined);
}

/** Sits outside every provider, so it reads the language directly. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // At most one automatic reload a minute: a later deploy is handled too, but a
    // version that is itself broken can't send the page into a reload loop.
    const lastReload = Number(sessionStorage.getItem(RELOADED_KEY) ?? 0);
    if (isStaleDeploy(error) && Date.now() - lastReload > 60_000) {
      sessionStorage.setItem(RELOADED_KEY, String(Date.now()));
      window.location.reload();
      return;
    }
    console.error('Render crash:', error, info.componentStack);
    report(error, info);
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
          onClick={() => window.location.reload()}
          className="h-11 rounded-full bg-accent px-5 text-sm font-semibold text-on-accent"
        >
          {m['error.crashBack']}
        </button>
      </div>
    );
  }
}
