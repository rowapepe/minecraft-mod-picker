import { useCallback, useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api, ApiError, type Mod } from "../api"
import { Composer } from "../components/Composer"
import { MenuIcon, SearchIcon } from "../components/Icons"
import { AnswerAvatar } from "../components/Logo"
import { ModCard } from "../components/ModCard"
import { Sidebar } from "../components/Sidebar"
import { ThemeToggle } from "../components/ThemeToggle"
import { clampQuery, isBlank } from "../library/query"
import { BASE } from "../mascot/costumes"
import { detectCostume } from "../mascot/detect"
import { MascotRow } from "../mascot/Mascot"

/** Сообщение чата: один запрос с состоянием и результатом (05, раздел 2.11). */
interface Message {
	id: number
	query: string
	status: "loading" | "done" | "error"
	mods: Mod[]
	answer: string | null
}

/** Чат: заголовок из первого сообщения и все сообщения по порядку (RULE-UI-11). */
interface Chat {
	id: number
	title: string
	messages: Message[]
}

const EXAMPLES = [
	"Хочу автоматизировать ферму и не получить лагов",
	"Нужен мод, чтобы удобно хранить много предметов",
	"Хочу улучшить производительность на слабом компьютере",
	"Ищу мод с новой генерацией мира и приключениями"
]

const isNarrow = () => !window.matchMedia("(min-width: 761px)").matches
const CHATS_KEY = "mod-picker-chats-v2"
const LEGACY_KEY = "mod-picker-history-v1"

const isMessage = (value: unknown): value is Message => {
	if (!value || typeof value !== "object") return false
	const m = value as Record<string, unknown>
	return (
		typeof m.id === "number" &&
		typeof m.query === "string" &&
		(m.status === "done" || m.status === "error") &&
		Array.isArray(m.mods) &&
		(m.answer === null || typeof m.answer === "string")
	)
}

const readChats = (): Chat[] => {
	try {
		const stored = localStorage.getItem(CHATS_KEY)
		if (stored) {
			const parsed = JSON.parse(stored) as unknown
			if (!Array.isArray(parsed)) return []
			return parsed
				.filter(
					(c): c is Chat =>
						!!c && typeof c === "object" && typeof (c as Chat).id === "number" && typeof (c as Chat).title === "string"
				)
				.map((c) => ({ ...c, messages: Array.isArray(c.messages) ? c.messages.filter(isMessage) : [] }))
				.filter((c) => c.messages.length > 0)
		}

		// Записи старого формата превращаются в чаты с одним сообщением.
		const legacy = localStorage.getItem(LEGACY_KEY)
		if (!legacy) return []
		const entries = JSON.parse(legacy) as unknown
		if (!Array.isArray(entries)) return []
		return entries
			.filter(isMessage)
			.map((m) => ({ id: m.id, title: m.query, messages: [m] }))
	} catch {
		return []
	}
}

/** Экран поиска пользователя (04, разделы 3–6). */
export function SearchPage() {
	const navigate = useNavigate()
	const [chats, setChats] = useState<Chat[]>(readChats)
	const [activeId, setActiveId] = useState<number | null>(null)
	const [draft, setDraft] = useState("")
	const [hint, setHint] = useState(false)
	const [sbOpen, setSbOpen] = useState(() => !isNarrow())
	const nextChatId = useRef(
		Math.max(0, ...chats.map((c) => c.id), ...chats.flatMap((c) => c.messages.map((m) => m.id))) + 1
	)
	const nextMessageId = useRef(Math.max(0, ...chats.flatMap((c) => c.messages.map((m) => m.id))) + 1)
	const feedRef = useRef<HTMLElement>(null)

	useEffect(() => {
		try {
			const saved = chats
				.map((c) => ({ ...c, messages: c.messages.filter((m) => m.status !== "loading") }))
				.filter((c) => c.messages.length > 0)
			localStorage.setItem(CHATS_KEY, JSON.stringify(saved))
		} catch {
			/* storage can be unavailable */
		}
	}, [chats])

	const active = chats.find((c) => c.id === activeId) ?? null
	const lastMessage = active?.messages[active.messages.length - 1] ?? null
	const loading = chats.some((c) => c.messages.some((m) => m.status === "loading"))
	const costume = lastMessage ? detectCostume(lastMessage.query) : BASE

	useEffect(() => {
		document.title = "Поиск модов"
	}, [])

	// Открытый чат показывается с последнего сообщения, новый ответ доскролливается.
	useEffect(() => {
		feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight })
	}, [activeId, active?.messages.length, lastMessage?.status])

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
			const chatId = active ? active.id : nextChatId.current++
			const messageId = nextMessageId.current++
			const message: Message = { id: messageId, query, status: "loading", mods: [], answer: null }

			setChats((list) => {
				if (list.some((c) => c.id === chatId)) {
					// Продолжение открытого чата: сообщение добавляется ниже (RULE-UI-11).
					return list.map((c) => (c.id === chatId ? { ...c, messages: [...c.messages, message] } : c))
				}
				return [{ id: chatId, title: query, messages: [message] }, ...list]
			})
			setActiveId(chatId)
			setDraft("")
			setHint(false)

			api
				.search(query)
				.then((r) =>
					setChats((list) =>
						list.map((c) =>
							c.id === chatId
								? {
										...c,
										messages: c.messages.map((m) =>
											m.id === messageId ? { ...m, status: "done", mods: r.mods, answer: r.answer } : m
										)
									}
								: c
						)
					)
				)
				.catch((err) => {
					if (err instanceof ApiError && err.status === 401) navigate("/login", { replace: true })
					setChats((list) =>
						list.map((c) =>
							c.id === chatId
								? { ...c, messages: c.messages.map((m) => (m.id === messageId ? { ...m, status: "error" } : m)) }
								: c
						)
					)
				})
		},
		[active, loading, navigate]
	)

	const logout = () => {
		api.logout().finally(() => navigate("/login", { replace: true }))
	}

	// Удаление чата (RULE-UI-13): активный чат закрывается, список сохраняется без записи.
	const deleteChat = (id: number) => {
		setChats((list) => list.filter((c) => c.id !== id))
		setActiveId((current) => (current === id ? null : current))
	}

	return (
		<div className="chat-app">
			<Sidebar
				open={sbOpen}
				items={chats.map((c) => ({ id: c.id, title: c.title }))}
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
				onDelete={deleteChat}
				onLogout={logout}
			/>

			<main className="chat-main">
				<header className="chat-header">
					<div className="chat-title-wrap">
						<button type="button" className="ibtn mob" onClick={() => setSbOpen(true)} aria-label="Открыть панель">
							<MenuIcon />
						</button>
						<h1 className="chat-title">{active ? active.title : "Новый поиск"}</h1>
					</div>
					<div className="header-actions">
						<span className="source-chip">Поиск по описаниям модов Modrinth</span>
						<ThemeToggle />
					</div>
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
								{active.messages.map((message) => (
									<div className="turn" key={message.id}>
										<div className="user-msg">{message.query}</div>
										<div className="answer-row">
											<AnswerAvatar />
											<div className="answer-col">
												<AnswerBody entry={message} />
											</div>
										</div>
									</div>
								))}
							</div>
						)}
					</div>
				</section>

				<footer className="composer-area">
					<div className="composer-inner">
						<MascotRow costume={costume} thinking={lastMessage?.status === "loading"} />
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

function AnswerBody({ entry }: { entry: Message }) {
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
