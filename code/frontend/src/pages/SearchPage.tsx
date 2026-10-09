import { useCallback, useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api, ApiError, type Mod } from "../api"
import { Composer } from "../components/Composer"
import { MenuIcon, SearchIcon } from "../components/Icons"
import { AnswerAvatar } from "../components/Logo"
import { ModCard } from "../components/ModCard"
import { Sidebar } from "../components/Sidebar"
import { clampQuery, isBlank } from "../library/query"
import { BASE } from "../mascot/costumes"
import { detectCostume } from "../mascot/detect"
import { MascotRow } from "../mascot/Mascot"

/** Запись сессии (05, раздел 2.11): живёт только в памяти вкладки. */
interface Entry {
	id: number
	query: string
	status: "loading" | "done" | "error"
	mods: Mod[]
	answer: string | null
}

const EXAMPLES = [
	"Хочу автоматизировать ферму и не получить лагов",
	"Нужен мод, чтобы удобно хранить много предметов",
	"Хочу улучшить производительность на слабом компьютере",
	"Ищу мод с новой генерацией мира и приключениями"
]

const isNarrow = () => !window.matchMedia("(min-width: 761px)").matches

/** Экран поиска пользователя (04, разделы 3–6). */
export function SearchPage() {
	const navigate = useNavigate()
	const [entries, setEntries] = useState<Entry[]>([])
	const [activeId, setActiveId] = useState<number | null>(null)
	const [draft, setDraft] = useState("")
	const [hint, setHint] = useState(false)
	const [sbOpen, setSbOpen] = useState(() => !isNarrow())
	const nextId = useRef(1)
	const feedRef = useRef<HTMLElement>(null)

	const active = entries.find((e) => e.id === activeId) ?? null
	const loading = entries.some((e) => e.status === "loading")
	const costume = active ? detectCostume(active.query) : BASE

	useEffect(() => {
		document.title = "Поиск модов"
	}, [])

	// Новый запрос или выбор записи: лента начинается с сообщения пользователя.
	useEffect(() => {
		feedRef.current?.scrollTo({ top: 0 })
	}, [activeId, active?.status])

	const closeIfNarrow = () => {
		if (isNarrow()) setSbOpen(false)
	}

	const run = useCallback(
		(text: string) => {
			if (loading) return
			if (isBlank(text)) {
				setHint(true) // GWT-02, GWT-03: запрос не отправляется, лента не меняется
				return
			}
			const query = text.trim()
			const id = nextId.current++
			setEntries((list) => [{ id, query, status: "loading", mods: [], answer: null }, ...list])
			setActiveId(id)
			setDraft("")
			setHint(false)
			api
				.search(query)
				.then((r) => setEntries((list) => list.map((e) => (e.id === id ? { ...e, status: "done", mods: r.mods, answer: r.answer } : e))))
				.catch((err) => {
					if (err instanceof ApiError && err.status === 401) navigate("/login", { replace: true })
					setEntries((list) => list.map((e) => (e.id === id ? { ...e, status: "error" } : e)))
				})
		},
		[loading, navigate]
	)

	const logout = () => {
		api.logout().finally(() => navigate("/login", { replace: true }))
	}

	return (
		<div className="chat-app">
			<Sidebar
				open={sbOpen}
				items={entries}
				activeId={activeId}
				onToggle={() => setSbOpen((v) => !v)}
				onNew={() => {
					setActiveId(null)
					setDraft("")
					setHint(false)
					closeIfNarrow()
				}}
				onPick={(id) => {
					setActiveId(id)
					closeIfNarrow()
				}}
				onLogout={logout}
			/>

			<main className="chat-main">
				<header className="chat-header">
					<div className="chat-title-wrap">
						<button type="button" className="ibtn mob" onClick={() => setSbOpen(true)} aria-label="Открыть панель">
							<MenuIcon />
						</button>
						<h1 className="chat-title">{active ? active.query : "Новый поиск"}</h1>
					</div>
					<span className="source-chip">Поиск по описаниям модов Modrinth</span>
				</header>

				<section className="feed scroll" ref={feedRef} aria-live="polite">
					<div className="feed-inner">
						{!active && (
							<div className="welcome">
								<div className="welcome-head">
									<h2>Что хотите сделать в игре?</h2>
									<p>Опишите задачу, и мы подберём подходящие моды.</p>
								</div>
								<div className="examples">
									{EXAMPLES.map((text) => (
										<button type="button" className="ex" key={text} onClick={() => run(text)} disabled={loading}>
											<span className="ex-icon">
												<SearchIcon />
											</span>
											<span>{text}</span>
										</button>
									))}
								</div>
							</div>
						)}

						{active && (
							<div className="thread-view">
								<div className="user-msg">{active.query}</div>
								<div className="answer-row">
									<AnswerAvatar />
									<div className="answer-col">
										<AnswerBody entry={active} />
									</div>
								</div>
							</div>
						)}
					</div>
				</section>

				<footer className="composer-area">
					<div className="composer-inner">
						<MascotRow costume={costume} thinking={active?.status === "loading"} />
						<Composer
							value={draft}
							loading={loading}
							hint={hint}
							onChange={(v) => {
								setDraft(clampQuery(v))
								setHint(false)
							}}
							onSubmit={() => run(draft)}
						/>
					</div>
				</footer>
			</main>
		</div>
	)
}

function AnswerBody({ entry }: { entry: Entry }) {
	if (entry.status === "loading") {
		return (
			<div role="status" className="loading-line">
				<span className="dots" aria-hidden="true">
					<span className="dot" />
					<span className="dot" />
					<span className="dot" />
				</span>
				<span>Ищем подходящие моды…</span>
			</div>
		)
	}
	if (entry.status === "error") {
		return (
			<p role="alert" className="msg msg-error">
				Не удалось выполнить поиск. Попробуйте ещё раз
			</p>
		)
	}
	if (entry.mods.length === 0) {
		return <p className="msg">Подходящих модов не найдено. Попробуйте описать задачу другими словами</p>
	}
	return (
		<div className="result">
			{entry.answer ? (
				<p className="answer-text">{entry.answer}</p>
			) : (
				<p className="msg">Объяснение сейчас недоступно, но вот найденные моды</p>
			)}
			<div className="mods">
				<div className="sb-label">Найденные моды</div>
				{entry.mods.map((m) => (
					<ModCard key={m.slug} mod={m} />
				))}
			</div>
			{entry.answer && <div className="footnote">Объяснение составлено только по описаниям найденных модов.</div>}
		</div>
	)
}
