# Minecraft Mod Picker

Помощник по подбору модов для Minecraft под задачу игрока: поиск по описаниям с Modrinth на собственной реализации BM25 и ответ с объяснением от LLM.

> Учебный проект НИРС 2026, МГТУ им. Н. Э. Баумана. Текущее состояние: [STATUS.md](STATUS.md).

## Команда

| Участник        | Зона ответственности                                                             |
| --------------- | -------------------------------------------------------------------------------- |
| Верзаков Никита | Продукт и интерфейс: задача, сценарии, документация Product, макет и внешний вид |
| Прощаев Алексей | Интеграция: связь интерфейса, поиска и вызова LLM                                |
| Кубанов Сергей  | RAG: корпус, индекс BM25, поиск и benchmark                                      |

## Основной сценарий

Игрок описывает задачу своими словами (например, «хочу автоматизировать ферму и не получить лагов») → система ищет подходящие моды по описаниям → показывает карточки модов и короткий ответ с объяснением, почему они подходят.

В приложении три экрана: вход, поиск (для пользователя) и админ-панель с числовой аналитикой (для администратора). Регистрации нет, учётных записей две: администратор и пользователь.

## Структура репозитория

```
minecraft-mod-picker/
├── README.md            описание и вход в проект
├── AGENTS.md            правила для кодингового агента
├── STATUS.md            состояние и следующий шаг
├── CHANGE_HISTORY.md    история изменений
├── docs/
│   ├── README.md        карта документов
│   ├── Product/         что строим: контекст, роли и сценарии, требования, интерфейс, правила
│   ├── Tech/            как устроено: архитектура, запуск, данные, API, проверки
│   ├── Service/         решения и вопросы, источники, протокол проверок
│   └── document-manifest.json
└── code/
    ├── scripts/         вспомогательные скрипты
    ├── data/            корпус описаний модов
    ├── frontend/        интерфейс (React + Vite + TypeScript)
    ├── backend/         интеграция, поиск, вызов LLM
    ├── tests/           тесты
    └── benchmark/       тестовые запросы и расчёт метрик
```

## Стек

Интерфейс — React + Vite + TypeScript. Бэкенд — Python + FastAPI. Поиск — собственный BM25 на Python. Подробности и обоснование: [docs/Tech/01-architecture.md](docs/Tech/01-architecture.md), решение `D-08`.

## Запуск

### Макет интерфейса

Нужны Node.js 20+ и npm.

```bash
cp .env.example .env     # в корне репозитория; значения для входа — в docs/Tech/02-running.md
cd code/frontend
npm install
npm run dev              # http://localhost:5173
```

Без `API_TARGET` `npm run dev` поднимает заглушку API только для разработки; с `API_TARGET=http://localhost:8000` интерфейс работает с бэкендом (ниже). Для локального входа: пользователь `player` / `player`, администратор `admin` / `admin` (впишите в `.env`). Подробности: [docs/Tech/02-running.md](docs/Tech/02-running.md).

### Бэкенд

Из каталога `code/`:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/uvicorn backend.main:app --reload --port 8000
```

`/api/search` ищет по корпусу собственным BM25; русский запрос перед поиском переводится через GigaChat (нужен `LLM_API_KEY`, `D-18`); по найденным модам GigaChat пишет объяснение или отказ (`D-19`). Подробности: [docs/Tech/02-running.md](docs/Tech/02-running.md).

### Поиск и benchmark

Нужен Python 3.12+. Команды выполняются из каталога `code/`:

```bash
python -m pip install -r search/requirements.txt
python -m search --explain "automate farm without lag"   # поиск по корпусу из 1000 модов
python -m benchmark.run                                  # Recall@5, MRR@5 → benchmark/results/
python -m pytest tests
```

Корпус выгружается заново командой `python3 code/scripts/fetch_modrinth.py` из корня (нужен `MODRINTH_USER_AGENT` в `.env`). Подробности: [docs/Tech/03-data.md](docs/Tech/03-data.md), [docs/Tech/05-verification.md](docs/Tech/05-verification.md).

## Документация

Карта документов: [docs/README.md](docs/README.md). Продуктовая часть: [docs/Product/README.md](docs/Product/README.md).

## Данные

Описания модов берутся из публичного API Modrinth. Источники: [docs/Service/sources.md](docs/Service/sources.md). Тексты описаний принадлежат авторам модов.

## Текущее состояние

Контрольная точка 1 пройдена: документация Product и интерфейс из трёх экранов в `code/frontend`. Для КТ2 готовы корпус из 1000 модов, собственный BM25 и benchmark поиска; бэкенд отдаёт выдачу BM25 с переводом запроса и объяснением через GigaChat (вход, аналитика, поиск, ответ).
