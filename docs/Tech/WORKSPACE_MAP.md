# Карта кода

| Путь                            | Назначение                                                     |
| ------------------------------- | -------------------------------------------------------------- |
| `code/scripts/`                 | Скрипты; `fetch_modrinth.py` — выгрузка корпуса с Modrinth     |
| `code/data/`                    | Корпус `mods.jsonl` и параметры выгрузки `mods.meta.json`      |
| `code/search/`                  | Предобработка и собственный индекс BM25, `python -m search`    |
| `code/frontend/`                | Интерфейс: React + Vite + TypeScript                           |
| `code/frontend/src/pages/`      | Экраны: вход, поиск, админ-панель                              |
| `code/frontend/src/components/` | Общие части интерфейса: логотип, значки, карточка мода, панель |
| `code/frontend/src/mascot/`     | Зомби, скелет, костюмы и выбор костюма по тексту               |
| `code/frontend/src/library/`    | Чистые функции: проверка запроса, форматирование, тема         |
| `code/frontend/src/styles/`     | Цвета и размеры (`tokens.css`), стили приложения               |
| `code/frontend/dev-stub/`       | Заглушка API для разработки (GAP-13), в сборку не входит       |
| `code/backend/`                 | Интеграция, поиск, вызов LLM (пока нет)                        |
| `code/tests/`                   | Тесты pytest для скриптов и поиска                             |
| `code/benchmark/`               | Корпус из 30 документов, вопросы, `python -m benchmark.run`    |
