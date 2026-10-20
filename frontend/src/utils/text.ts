/** Wrap text in Unicode isolate marks so Hebrew inside an English sentence (or
 *  the reverse) keeps its own direction instead of reordering its neighbors. */
export function isolate(text: string): string {
  return `⁨${text}⁩`;
}

/** "2 חלב 3%" -> "חלב 3%", "חצי קילו עגבניות" -> "עגבניות", "bananas 1kg" -> "bananas". */
export function itemName(line: string): string {
  return line
    .replace(/^\s*[\d.,]+\s*(×|x)?\s*/i, '')
    .replace(/^(חצי\s+)?קילו\s+/, '')
    .replace(/\s*[\d.,]*\s*(kg|ק"ג|ק״ג|קילו)\s*$/i, '')
    .trim();
}
