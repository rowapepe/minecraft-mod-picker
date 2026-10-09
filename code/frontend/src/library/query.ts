/** Максимальная длина запроса (RULE-UI-02). */
export const MAX_QUERY_LENGTH = 500;

/** Пустой запрос и запрос из одних пробелов не отправляются (RULE-UI-01). */
export function isBlank(text: string): boolean {
  return text.trim().length === 0;
}

/** Поле не принимает лишние символы (GWT-04). */
export function clampQuery(text: string): string {
  return text.length > MAX_QUERY_LENGTH ? text.slice(0, MAX_QUERY_LENGTH) : text;
}

/** Подпись записи в боковой панели: до 36 символов с многоточием (04, раздел 3.1). */
export function shortTitle(text: string, max = 36): string {
  const t = text.trim().replace(/\s+/g, ' ');
  return t.length > max ? `${t.slice(0, max)}…` : t;
}
