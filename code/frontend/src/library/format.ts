/** Число запросов с пробелами между группами цифр (04, раздел 8.2). */
export function formatCount(n: number): string {
  return n.toLocaleString('ru-RU');
}

/** Доля запросов без результатов в процентах (RULE-ADM-06). */
export function formatPercent(part: number, total: number): string {
  if (!total || !Number.isFinite(part) || part <= 0) return '0%';
  return new Intl.NumberFormat('ru-RU', { style: 'percent', maximumFractionDigits: 0 })
    .format(part / total)
    .replace(/\s/g, '');
}

/** Подпись дня в графике «Запросы по дням»: дата вида ГГГГ-ММ-ДД. */
export function formatDay(date: string): string {
  const parsed = new Date(`${date}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return date;
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' }).format(parsed);
}
