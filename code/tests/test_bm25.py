"""BM25 на маленьком корпусе с известным ответом (`Tech/05-verification`, КТ2).

Числа взяты из презентации «Занятие 3» (слайды 8–28) и методички (разделы 1.3–1.4).
"""

import json
from math import log

import pytest

from search import BM25Index, ModSearch, Preprocessor, lemmatize_en, no_lemmatize, tokenize

LECTURE_DOCS = [
    ("A", "Возврат оплаты на карту."),
    ("B", "Статус оплаты в приложении."),
    ("C", "Возврат билета через кассу."),
]
LECTURE_QUERY = "Как происходит возврат оплаты?"


@pytest.fixture
def lecture():
    # на слайдах слова сравниваются буквально, без лемматизации (слайд 9)
    return BM25Index.build(LECTURE_DOCS, preprocess=Preprocessor(no_lemmatize), k1=1.2, b=0.75)


# ------------------------------------------------------------- предобработка


def test_tokenize_lowercase_and_words():
    # слайд 9: нижний регистр, без пунктуации
    assert tokenize("Возврат оплаты на карту.") == ["возврат", "оплаты", "на", "карту"]
    assert tokenize("Sodium: FPS-boost, 2x faster! (1.20.1)") == [
        "sodium", "fps", "boost", "2x", "faster", "1", "20", "1"
    ]
    assert tokenize("  ...  ") == []


def test_without_lemmatization_word_forms_differ():
    # слайд 9: «билет» ≠ «билета»
    pre = Preprocessor(no_lemmatize)
    assert pre("билет") != pre("билета")


def test_english_lemmatization():
    pre = Preprocessor(lemmatize_en)
    assert pre("Automated Farms with Mobs and Shaders") == [
        "automate", "farm", "with", "mob", "and", "shader"
    ]
    assert pre("farming") == pre("farm") == ["farm"]
    # слова не из словаря не меняются
    assert pre("Sodium фермы") == ["sodium", "фермы"]


# ------------------------------------------------------------------- индекс


def test_inverted_index_and_lengths(lecture):
    # слайды 10 и 12
    assert lecture.index["возврат"] == {"A": 1, "C": 1}
    assert lecture.index["оплаты"] == {"A": 1, "B": 1}
    assert lecture.lengths == {"A": 4, "B": 4, "C": 4}
    assert lecture.N == 3
    assert lecture.avgdl == 4


def test_methodology_index_example():
    # методичка, раздел 1.4: документы уже после предобработки
    docs = [
        ("d1", "лапласиан граф использоваться анализ структура"),
        ("d2", "матрица смежность граф описывать связь вершина"),
        ("d3", "метод машинный обучение использовать матрица данные"),
    ]
    idx = BM25Index.build(docs, preprocess=Preprocessor(no_lemmatize))
    assert set(idx.index["лапласиан"]) == {"d1"}
    assert set(idx.index["граф"]) == {"d1", "d2"}
    assert set(idx.index["матрица"]) == {"d2", "d3"}
    assert set(idx.index["обучение"]) == {"d3"}


def test_duplicate_doc_id_rejected(lecture):
    with pytest.raises(ValueError):
        lecture.add("A", "ещё раз")


# --------------------------------------------------------------------- баллы


def test_idf_lecture_value(lecture):
    # слайд 13: ln(1 + (3 − 2 + 0,5) / (2 + 0,5)) ≈ 0,470
    assert lecture.idf("возврат") == pytest.approx(log(1.6))
    assert round(lecture.idf("возврат"), 3) == 0.470
    # слово, которого нет в корпусе, тоже имеет положительный IDF, но не даёт вклада
    assert lecture.idf("как") > 0


def test_scores_lecture_example(lecture):
    # слайды 21–24
    hits = lecture.score(LECTURE_QUERY)
    assert set(hits) == {"A", "B", "C"}
    assert round(hits["A"].score, 3) == 0.940
    assert round(hits["B"].score, 3) == 0.470
    assert round(hits["C"].score, 3) == 0.470
    # слайд 17: «как», «происходит» — вклад 0, в разборе их нет
    assert set(hits["A"].contributions) == {"возврат", "оплаты"}


def test_top_k_and_ties_by_id(lecture):
    # слайд 24: k = 2 → A и B; равные баллы упорядочиваем по ID
    assert [h.doc_id for h in lecture.search(LECTURE_QUERY, k=2)] == ["A", "B"]
    assert [h.doc_id for h in lecture.search(LECTURE_QUERY, k=5)] == ["A", "B", "C"]


def test_repeated_query_words_counted_once(lecture):
    # слайд 26: dict.fromkeys(tokens(query))
    once = lecture.score("возврат")["A"].score
    assert lecture.score("возврат возврат возврат")["A"].score == pytest.approx(once)


def test_term_frequency_saturation():
    # слайд 14: при равной длине 1 раз → 1,00, 2 раза → 1,38 (k1 = 1,2)
    docs = [("x", "a a b c"), ("y", "a b c d"), ("z", "e f g h")]
    idx = BM25Index.build(docs, preprocess=Preprocessor(no_lemmatize), k1=1.2, b=0.75)
    hits = idx.score("a")
    ratio = hits["x"].score / hits["y"].score
    assert round(ratio, 2) == 1.38


def test_length_normalization():
    # слайд 15: при одинаковом tf длинный документ получает меньше
    docs = [("short", "farm wheat"), ("long", "farm " + "word " * 10)]
    idx = BM25Index.build(docs, preprocess=Preprocessor(no_lemmatize))
    hits = idx.score("farm")
    assert hits["short"].score > hits["long"].score
    # при b = 0 длина не учитывается
    flat = BM25Index.build(docs, preprocess=Preprocessor(no_lemmatize), b=0)
    flat_hits = flat.score("farm")
    assert flat_hits["short"].score == pytest.approx(flat_hits["long"].score)


def test_no_match_and_empty_query(lecture):
    # RULE-SRCH-05: документы с нулевой оценкой в выдачу не попадают
    assert lecture.search("наличные") == []
    assert lecture.search("") == []
    assert lecture.search("?!") == []
    assert BM25Index(preprocess=Preprocessor(no_lemmatize)).search("возврат") == []


def test_save_and_load_roundtrip(lecture, tmp_path):
    path = tmp_path / "index.json"
    lecture.meta = {"corpus": "lecture"}
    lecture.save(path)
    loaded = BM25Index.load(path, preprocess=Preprocessor(no_lemmatize))
    assert loaded.meta == {"corpus": "lecture"}
    assert (loaded.k1, loaded.b) == (1.2, 0.75)
    assert [(h.doc_id, round(h.score, 6)) for h in loaded.search(LECTURE_QUERY)] == [
        (h.doc_id, round(h.score, 6)) for h in lecture.search(LECTURE_QUERY)
    ]
    # индекс с другой предобработкой запросов не загружается
    with pytest.raises(ValueError):
        BM25Index.load(path, preprocess=Preprocessor(lemmatize_en))


# ------------------------------------------------------------ корпус модов


def write_corpus(path, docs):
    path.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")


MODS = [
    {"id": "m1", "title": "Farm Helper", "description": "Automatic crop farms", "body": "Harvests farms."},
    {"id": "m2", "title": "Sodium", "description": "Rendering optimization", "body": "Improves FPS, less lag."},
    {"id": "m3", "title": "Storage Drawers", "description": "Store many items", "body": "Drawers for storage."},
]


def test_mod_search_uses_title_description_body(tmp_path):
    corpus = tmp_path / "mods.jsonl"
    write_corpus(corpus, MODS)
    engine = ModSearch.build(corpus)
    # «farming» → farm (лемматизация), совпадает с title, description и body m1
    assert [d["id"] for d, _ in engine.search("automatic farming")] == ["m1"]
    assert [d["id"] for d, _ in engine.search("fps lag")] == ["m2"]
    assert engine.search("magic spells") == []


def test_mod_search_open_rebuilds_when_corpus_changes(tmp_path):
    corpus, index = tmp_path / "mods.jsonl", tmp_path / "index.json"
    write_corpus(corpus, MODS)
    first = ModSearch.open(corpus, index)
    assert index.is_file()
    assert ModSearch.open(corpus, index).index.meta == first.index.meta  # загружен из файла
    write_corpus(corpus, MODS + [{"id": "m4", "title": "Magic Spells", "description": "", "body": ""}])
    assert [d["id"] for d, _ in ModSearch.open(corpus, index).search("magic")] == ["m4"]
