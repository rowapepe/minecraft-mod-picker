"""Предварительная обработка текста для BM25 (RULE-SRCH-02, RULE-SRCH-07).

Шаги — по методическим указаниям (разделы 1.1–1.2) и презентации
«Занятие 3», слайд 9; обоснование выбора — `docs/Tech/03-data.md`:

1. приведение к нижнему регистру;
2. токенизация: токен — отдельное слово, то есть непрерывная
   последовательность букв и цифр; пунктуация и прочие символы — разделители;
3. лемматизация готовой библиотекой `simplemma` (английский словарь),
   что методичка допускает явно (раздел 2).

Стоп-слова по умолчанию не удаляются: в BM25 частые слова получают малый IDF
сами (как «как» и «происходит» в примере на слайде 11). Удаление стоп-слов
включается параметром `stopwords` и проверяется на benchmark.

Запрос проходит ту же обработку, что и документы (методичка, замечание 1.1).
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Callable

_TOKEN = re.compile(r"[^\W_]+")  # буквы и цифры любого алфавита

Lemmatizer = Callable[[str], str]


def tokenize(text: str) -> list[str]:
    """Нижний регистр и разбиение на слова."""
    return _TOKEN.findall(text.lower())


@lru_cache(maxsize=None)
def lemmatize_en(word: str) -> str:
    """Начальная форма английского слова: farms → farm, mobs → mob.

    Слова, которых нет в словаре (названия модов, русские слова), не меняются.
    """
    import simplemma  # импорт здесь: модуль токенизации работает и без библиотеки

    return simplemma.lemmatize(word, lang="en").lower()


def no_lemmatize(word: str) -> str:
    """Без лемматизации: слова сравниваются буквально (как на слайде 9)."""
    return word


# Служебные слова английского языка: местоимения, артикли, предлоги, союзы,
# вспомогательные глаголы. Используются только в эксперименте benchmark
# «удаление стоп-слов»; в базовой настройке стоп-слова не удаляются.
ENGLISH_STOPWORDS = frozenset("""
a about above after again against all am an and any are as at be been before being below
between both but by can could did do does doing down during each few for from further had
has have having he her here hers herself him himself his how i if in into is it its itself
just me more most my myself no nor not now of off on once only or other our ours ourselves
out over own same she should so some such than that the their theirs them themselves then
there these they this those through to too under until up very was we were what when where
which while who whom why will with would you your yours yourself yourselves
""".split())


class Preprocessor:
    """Текст → список термов. Один и тот же объект обрабатывает документы и запросы."""

    def __init__(self, lemmatizer: Lemmatizer = lemmatize_en, stopwords: frozenset[str] = frozenset()):
        self.lemmatizer = lemmatizer
        self.stopwords = stopwords

    @property
    def name(self) -> str:
        names = {lemmatize_en: "simplemma-en", no_lemmatize: "none"}
        name = "lower+words+" + names.get(self.lemmatizer, getattr(self.lemmatizer, "__name__", "custom"))
        return name + (f"+stop{len(self.stopwords)}" if self.stopwords else "")

    def __call__(self, text: str) -> list[str]:
        terms = []
        for token in tokenize(text):
            if token in self.stopwords:
                continue
            lemma = self.lemmatizer(token)
            if lemma not in self.stopwords:  # is, was → be
                terms.append(lemma)
        return terms
