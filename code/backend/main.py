"""Каркас API Minecraft Mod Picker. Контракт: `docs/Tech/04-api-and-access.md`.

Этап каркаса: `/api/search` не вызывает индекс и LLM, а отвечает проверочным
сообщением о том, что запрос дошёл до сервера (`D-16`).

Запуск из `code/`:  uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .auth import COOKIE_NAME, Role, check_credentials, make_session, read_session
from .config import Settings
from .stats import Stats

MAX_QUERY_LENGTH = 500  # RULE-UI-02


class LoginBody(BaseModel):
    login: str
    password: str


class SearchBody(BaseModel):
    query: str


class Mod(BaseModel):
    slug: str
    title: str
    description: str
    categories: list[str]
    url: str


class SearchResponse(BaseModel):
    mods: list[Mod]
    answer: str | None


def echo_search(query: str) -> SearchResponse:
    """Проверочный ответ каркаса вместо поиска BM25 и LLM.

    Карточка нужна, чтобы интерфейс показал ответ: при пустом `mods` он
    выводит «ничего не найдено» и не показывает `answer`.
    """
    return SearchResponse(
        answer=f"Бэкенд получил запрос «{query}». Поиск и LLM пока не подключены: это проверочный ответ каркаса.",
        mods=[
            Mod(
                slug="backend-check",
                title="Бэкенд на связи",
                description="Служебная карточка: запрос дошёл от интерфейса до сервера и вернулся обратно.",
                categories=["Служебное"],
                url="https://modrinth.com/mods",
            )
        ],
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()
    stats = Stats(settings.db_path)
    app = FastAPI(title="Minecraft Mod Picker API", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.state.settings = settings
    app.state.stats = stats

    @app.exception_handler(RequestValidationError)
    async def bad_request(_: Request, __: RequestValidationError) -> JSONResponse:
        return JSONResponse({"detail": "Некорректный запрос"}, status_code=400)

    @app.exception_handler(Exception)
    async def server_error(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse({"detail": "Не удалось выполнить поиск"}, status_code=500)  # RULE-ERR-01

    def current_role(request: Request) -> Role:
        role = read_session(settings, request.cookies.get(COOKIE_NAME))
        if role is None:
            raise HTTPException(401, "Вход не выполнен")
        return role

    def require(role: Role):
        def dependency(actual: Role = Depends(current_role)) -> Role:
            if actual != role:
                raise HTTPException(403, "Нет доступа")
            return actual

        return dependency

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/api/auth/login")
    def login(body: LoginBody, response: Response) -> dict:
        role = check_credentials(settings, body.login, body.password)
        if role is None:
            raise HTTPException(401, "Неверный логин или пароль")
        stats.record_login()  # RULE-ADM-04
        # Без Max-Age: сессия живёт до выхода или закрытия браузера (GAP-11).
        response.set_cookie(COOKIE_NAME, make_session(settings, role), httponly=True, samesite="lax", path="/")
        return {"role": role}

    @app.post("/api/auth/logout", status_code=204)
    def logout(_: Role = Depends(current_role)) -> Response:
        response = Response(status_code=204)
        response.delete_cookie(COOKIE_NAME, path="/")
        return response

    @app.get("/api/auth/me")
    def me(role: Role = Depends(current_role)) -> dict:
        return {"role": role}

    @app.post("/api/search", response_model=SearchResponse)
    def search(body: SearchBody, _: Role = Depends(require("user"))) -> SearchResponse:
        query = body.query.strip()
        if not query or len(body.query) > MAX_QUERY_LENGTH:  # RULE-UI-01, RULE-UI-02
            raise HTTPException(400, "Пустой или слишком длинный запрос")
        result = echo_search(query)
        stats.record_search(empty=not result.mods)  # RULE-ADM-02, RULE-ADM-06
        return result

    @app.get("/api/admin/stats")
    def admin_stats(_: Role = Depends(require("admin"))) -> dict:
        return stats.snapshot()

    return app


def __getattr__(name: str):
    # `uvicorn backend.main:app` — приложение создаётся при первом обращении,
    # чтобы импорт модуля в тестах не читал .env и не открывал базу.
    if name == "app":
        globals()["app"] = create_app()
        return globals()["app"]
    raise AttributeError(name)
