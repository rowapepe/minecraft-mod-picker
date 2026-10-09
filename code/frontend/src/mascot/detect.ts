import { BASE, COSTUMES, type Costume } from './costumes';

/** Слова запроса: нижний регистр, `ё` → `е`, разделители — всё, кроме букв и цифр (05, раздел 2.10). */
export function wordsOf(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/ё/g, 'е')
    .split(/[^\p{L}\p{N}]+/u)
    .filter(Boolean);
}

function matches(word: string, keyword: string): boolean {
  return keyword.endsWith('$') ? word === keyword.slice(0, -1) : word.startsWith(keyword);
}

/**
 * Костюм зомби по тексту запроса (RULE-MASCOT-02): выигрывает костюм с наибольшим числом
 * совпавших слов, при равенстве — стоящий выше в таблице, без совпадений — без костюма.
 */
export function detectCostume(text: string): Costume {
  const words = wordsOf(text);
  let best: Costume = BASE;
  let bestScore = 0;
  for (const costume of COSTUMES) {
    const score = words.filter((w) => costume.keywords.some((k) => matches(w, k))).length;
    if (score > bestScore) {
      best = costume;
      bestScore = score;
    }
  }
  return best;
}
