import { isAxiosError } from 'axios';

/** A message the user can read, from any API failure. */
export function getErrorMessage(err: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (isAxiosError(err)) {
    if (!err.response) return 'Cannot reach CartWise right now. Check your connection.';
    const detail: unknown = err.response.data?.detail;
    if (typeof detail === 'string') return detail;
    // FastAPI validation errors: [{ msg: "..." }, ...]
    if (Array.isArray(detail) && detail.length > 0 && typeof detail[0]?.msg === 'string') {
      return detail[0].msg.replace(/^Value error, /, '');
    }
    if (err.response.status === 429) return 'Too many requests. Please wait a minute and try again.';
  }
  return fallback;
}
