import { AxiosError, AxiosHeaders, type AxiosResponse } from 'axios';
import { describe, expect, it } from 'vitest';
import type { MessageKey } from '../i18n/en';
import { getErrorCode, getErrorMessage } from './errors';

// Returns the key itself, so tests assert which message was chosen, not its wording.
const t = (key: MessageKey, vars?: Record<string, string | number>) => (vars ? `${key} ${JSON.stringify(vars)}` : key);

function apiError(status: number, data: unknown = {}, headers: Record<string, string> = {}): AxiosError {
  const response = { status, data, headers, statusText: '', config: { headers: new AxiosHeaders() } } as AxiosResponse;
  return new AxiosError('Request failed', 'ERR_BAD_RESPONSE', undefined, undefined, response);
}

describe('getErrorMessage', () => {
  it('translates the server code instead of showing its English detail', () => {
    expect(getErrorMessage(apiError(409, { code: 'email_taken', detail: 'Email already registered' }), t)).toBe('error.code.email_taken');
  });

  it('tells the user how many seconds to wait when rate limited', () => {
    expect(getErrorMessage(apiError(429, { retry_after: 42 }), t)).toBe('error.rateLimited {"seconds":42}');
    expect(getErrorMessage(apiError(429, {}, { 'retry-after': '7' }), t)).toBe('error.rateLimited {"seconds":7}');
    expect(getErrorMessage(apiError(429), t)).toBe('error.tooMany');
  });

  it("treats the host's bare 502 as a server error, not a raw HTML page", () => {
    expect(getErrorMessage(apiError(502, '<html>Bad Gateway</html>'), t)).toBe('error.code.server_error');
  });

  it('separates a timeout from being offline', () => {
    expect(getErrorMessage(new AxiosError('timeout', 'ECONNABORTED'), t)).toBe('error.timeout');
    expect(getErrorMessage(new AxiosError('Network Error', 'ERR_NETWORK'), t)).toBe('error.offline');
  });

  it('names the field behind a validation error', () => {
    const weak = apiError(422, { detail: [{ loc: ['body', 'password'], msg: 'too short' }] });
    const other = apiError(422, { detail: [{ loc: ['body', 'name'], msg: 'missing' }] });
    expect(getErrorMessage(weak, t)).toBe('error.code.weak_password');
    expect(getErrorMessage(other, t)).toBe('error.code.invalid_input');
  });

  it('falls back to the server detail for an unknown code, then to the fallback', () => {
    expect(getErrorMessage(apiError(400, { code: 'brand_new_code', detail: 'Plain detail' }), t)).toBe('Plain detail');
    expect(getErrorMessage(new Error('not from axios'), t, 'error.generic')).toBe('error.generic');
  });
});

describe('getErrorCode', () => {
  it('reads only a string code', () => {
    expect(getErrorCode(apiError(404, { code: 'store_not_found' }))).toBe('store_not_found');
    expect(getErrorCode(apiError(404, { code: 7 }))).toBeNull();
    expect(getErrorCode(new Error('x'))).toBeNull();
  });
});
