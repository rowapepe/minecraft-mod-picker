/** Число запросов с пробелами между группами цифр (04, раздел 8.2). */
export function formatCount(n: number): string {
  return n.toLocaleString('ru-RU');
}
