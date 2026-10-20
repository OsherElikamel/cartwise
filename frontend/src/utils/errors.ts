import { isAxiosError } from 'axios';
import en, { type MessageKey } from '../i18n/en';

type Translate = (key: MessageKey, vars?: Record<string, string | number>) => string;

function isMessageKey(key: string): key is MessageKey {
  return key in en;
}

/** The server's error code, if the response carried one. */
export function getErrorCode(err: unknown): string | null {
  if (!isAxiosError(err)) return null;
  const code: unknown = err.response?.data?.code;
  return typeof code === 'string' ? code : null;
}

/** A message the user can read, in their language, from any API failure.
 *  The server sends a stable `code`; its English `detail` is only a fallback. */
export function getErrorMessage(err: unknown, t: Translate, fallback: MessageKey = 'error.generic'): string {
  if (!isAxiosError(err)) return t(fallback);
  if (err.code === 'ECONNABORTED') return t('error.timeout');
  if (!err.response) return t('error.offline');

  const data = err.response.data ?? {};
  if (err.response.status === 429) {
    const seconds = Number(data.retry_after ?? err.response.headers['retry-after']);
    return Number.isFinite(seconds) && seconds > 0 ? t('error.rateLimited', { seconds }) : t('error.tooMany');
  }

  const code = getErrorCode(err);
  if (code) {
    const key = `error.code.${code}`;
    if (isMessageKey(key)) return t(key);
  }

  // FastAPI validation errors: [{ loc: ["body", "password"], msg: "..." }, ...]
  if (err.response.status === 422 && Array.isArray(data.detail)) {
    const field = String(data.detail[0]?.loc?.at(-1) ?? '');
    if (field === 'password') return t('error.code.weak_password');
    if (field === 'email') return t('error.code.invalid_email');
    return t('error.code.invalid_input');
  }

  return typeof data.detail === 'string' ? data.detail : t(fallback);
}
