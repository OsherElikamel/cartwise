// Mirrors the backend's Pydantic schemas. Money arrives as decimal strings
// (exact, never floats) and is only formatted for display.

export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface Store {
  id: string;
  chain_slug: string;
  chain_name: string;
  store_code: string;
  name: string;
  address: string | null;
  is_tracked: boolean;
  is_demo: boolean;
  is_ready: boolean;
}

export interface Chain {
  id: string;
  slug: string;
  name: string;
  name_he: string;
  store_count: number;
  tracked_store_count: number;
}

export type Unit = 'unit' | 'kg';

export interface ParsedItem {
  original: string;
  search_terms: string[];
  quantity: number;
  unit: Unit;
  brand: string | null;
  size: string | null;
}

export type Confidence = 'high' | 'low' | 'remembered';

export interface Alternative {
  item_code: string;
  name: string;
  price: string;
}

export interface BasketLine {
  index: number;
  match_key: string;
  item_code: string | null;
  name: string | null;
  is_weighted: boolean | null;
  regular_price: string | null;
  line_total: string | null;
  deal: string | null;
  confidence: Confidence | null;
  reason: string | null;
  alternatives: Alternative[];
}

export interface StoreBasket {
  store_id: string;
  chain_slug: string;
  chain_name: string;
  store_name: string;
  shared_total: string;
  full_total: string;
  missing: number[];
  lines: BasketLine[];
}

export interface BasketComparison {
  items: ParsedItem[];
  shared_items: number[];
  stores: StoreBasket[];
  savings_vs_most_expensive: string;
  remembered_matches: number;
  ai_matches: number;
}

export interface Pick {
  store_id: string;
  index: number;
  item_code: string;
  confidence: Confidence;
  reason: string;
}

export interface SavedList {
  id: string;
  name: string;
  text: string;
  is_parsed: boolean;
  updated_at: string;
}

export interface RunSummary {
  id: string;
  list_id: string | null;
  list_name: string | null;
  item_count: number;
  cheapest_chain: string;
  cheapest_total: string;
  savings: string;
  created_at: string;
}

export interface RunDetail extends RunSummary {
  result: BasketComparison;
}
