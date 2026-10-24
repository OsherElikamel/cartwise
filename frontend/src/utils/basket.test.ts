import { describe, expect, it } from 'vitest';
import type { BasketComparison, BasketLine } from '../types';
import { markRemembered, toPicks } from './basket';

function line(index: number, item_code: string | null, confidence: BasketLine['confidence']): BasketLine {
  return {
    index, match_key: `k${index}`, item_code, name: null, is_weighted: false, regular_price: null,
    line_total: null, deal: null, confidence, reason: 'AI pick', alternatives: [],
  };
}

const result: BasketComparison = {
  items: [], shared_items: [0, 1], savings_vs_most_expensive: '0', remembered_matches: 0, ai_matches: 2,
  stores: [{
    store_id: 's1', chain_slug: 'rami-levy', chain_name: 'Rami Levy', store_name: 'Ashdod',
    shared_total: '0', full_total: '0', missing: [2],
    lines: [line(0, '111', 'high'), line(1, '222', 'low'), line(2, null, null)],
  }],
};

describe('toPicks', () => {
  it('keeps every matched line and skips lines with no product', () => {
    expect(toPicks(result).map((p) => p.item_code)).toEqual(['111', '222']);
  });

  it("puts the user's choice in place of one line", () => {
    const picks = toPicks(result, { storeId: 's1', index: 1, itemCode: '333', confidence: 'high' });
    expect(picks[1]).toMatchObject({ index: 1, item_code: '333', reason: 'You chose this' });
    expect(picks[0].item_code).toBe('111');
  });
});

describe('markRemembered', () => {
  it('marks only that line and leaves the original result untouched', () => {
    const updated = markRemembered(result, 's1', 1);
    expect(updated.stores[0].lines.map((l) => l.confidence)).toEqual(['high', 'remembered', null]);
    expect(result.stores[0].lines[1].confidence).toBe('low');
  });
});
