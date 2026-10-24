import { describe, expect, it } from 'vitest';
import { isolate, itemName } from './text';

describe('itemName', () => {
  it.each([
    ['2 חלב 3%', 'חלב 3%'],
    ['3 × במבה', 'במבה'],
    ['חצי קילו עגבניות', 'עגבניות'],
    ['קילו פרגיות', 'פרגיות'],
    ['bananas 1kg', 'bananas'],
    ['עגבניות 2 ק"ג', 'עגבניות'],
    ['ביצים L', 'ביצים L'],
  ])('%s -> %s', (line, name) => {
    expect(itemName(line)).toBe(name);
  });
});

describe('isolate', () => {
  it('wraps text in first-strong isolate marks', () => {
    expect(isolate('חלב')).toBe('⁨חלב⁩');
  });
});
