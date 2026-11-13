import { describe, expect, it } from 'vitest';
import { MAX_QUERY_LENGTH, clampQuery, isBlank, shortTitle } from './query';
import { formatCount, formatDay, formatPercent } from './format';

describe('проверка запроса', () => {
  it('пустой и пробельный запрос — пустой (RULE-UI-01)', () => {
    expect(isBlank('')).toBe(true);
    expect(isBlank('   \n\t ')).toBe(true);
    expect(isBlank(' ферма ')).toBe(false);
  });

  it('обрезает до 500 символов (RULE-UI-02, GWT-04)', () => {
    expect(MAX_QUERY_LENGTH).toBe(500);
    expect(clampQuery('а'.repeat(700))).toHaveLength(500);
    expect(clampQuery('короткий')).toBe('короткий');
  });

  it('сокращает подпись записи до 36 символов', () => {
    expect(shortTitle('ферма')).toBe('ферма');
    expect(shortTitle('а'.repeat(40))).toBe(`${'а'.repeat(36)}…`);
    expect(shortTitle('  много   пробелов  ')).toBe('много пробелов');
  });
});

describe('formatCount', () => {
  it('ноль и группы цифр', () => {
    expect(formatCount(0)).toBe('0');
    expect(formatCount(1284).replace(/\s/g, ' ')).toBe('1 284');
  });
});

describe('formatPercent (RULE-ADM-06)', () => {
  it('доля в процентах с округлением до целого', () => {
    expect(formatPercent(5, 42)).toBe('12%');
    expect(formatPercent(1, 4)).toBe('25%');
  });

  it('ноль при отсутствии запросов', () => {
    expect(formatPercent(0, 0)).toBe('0%');
    expect(formatPercent(3, 0)).toBe('0%');
  });
});

describe('formatDay', () => {
  it('подписывает дату и не падает на некорректной', () => {
    expect(formatDay('2026-11-13')).toMatch(/13/);
    expect(formatDay('не дата')).toBe('не дата');
  });
});
