import { isAxiosError } from 'axios';
import type { MessageKey } from '../i18n/en';

type Translate = (key: MessageKey) => string;

/** A message the user can read, from any API failure. Server messages are shown as sent. */
export function getErrorMessage(err: unknown, t: Translate, fallback: MessageKey = 'error.generic'): string {
  if (isAxiosError(err)) {
    if (!err.response) return t('error.offline');
    if (err.response.status === 429) return t('error.tooMany');
    const detail: unknown = err.response.data?.detail;
    if (typeof detail === 'string') return detail;
    // FastAPI validation errors: [{ msg: "..." }, ...]
    if (Array.isArray(detail) && detail.length > 0 && typeof detail[0]?.msg === 'string') {
      return detail[0].msg.replace(/^Value error, /, '');
    }
  }
  return t(fallback);
}
