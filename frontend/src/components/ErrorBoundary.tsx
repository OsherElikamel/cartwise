import { Component, type ErrorInfo, type ReactNode } from 'react';

interface State {
  hasError: boolean;
}

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
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="text-lg font-semibold">Something broke on this page.</p>
        <p className="text-sm text-app-text-secondary">Your lists and choices are safe. Reloading usually fixes it.</p>
        <button
          type="button"
          onClick={() => window.location.assign('/')}
          className="h-11 rounded-xl bg-accent px-5 text-sm font-semibold text-on-accent"
        >
          Back to CartWise
        </button>
      </div>
    );
  }
}
