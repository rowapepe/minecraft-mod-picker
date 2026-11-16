import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api, type StatsResponse } from "../api"
import { AlertIcon, ChatIcon, CheckIcon, CrossIcon, LogoutIcon, SearchIcon, UserIcon } from "../components/Icons"
import { LogoMark } from "../components/Logo"
import { ThemeToggle } from "../components/ThemeToggle"
import { formatCount, formatDay, formatPercent } from "../library/format"

type Stats = { state: "loading" } | { state: "error" } | { state: "ready"; data: StatsResponse }

const REFRESH_MS = 10_000

/** Админ-панель (04, раздел 8): числовая аналитика (RULE-ADM-01…07). */
export function AdminPage() {
	const navigate = useNavigate()
	const [stats, setStats] = useState<Stats>({ state: "loading" })
	const [updatedAt, setUpdatedAt] = useState<Date | null>(null)

	useEffect(() => {
		document.title = "Админ-панель"
		let alive = true
		let inFlight = false
		let timer: number | undefined

		const load = async () => {
			if (inFlight) return
			inFlight = true
			try {
				const data = await api.stats()
				if (!alive) return
				setStats({ state: "ready", data })
				setUpdatedAt(new Date())
			} catch {
				// При ошибке обновления последние числа остаются на экране (RULE-ADM-07).
				if (alive) setStats((prev) => (prev.state === "ready" ? prev : { state: "error" }))
			} finally {
				inFlight = false
			}
		}

		void load()
		timer = window.setInterval(() => {
			if (document.visibilityState === "visible") void load()
		}, REFRESH_MS)

		const onVisibility = () => {
			if (document.visibilityState === "visible") void load()
		}
		document.addEventListener("visibilitychange", onVisibility)

		return () => {
			alive = false
			if (timer !== undefined) window.clearInterval(timer)
			document.removeEventListener("visibilitychange", onVisibility)
		}
	}, [])

	const logout = () => {
		api.logout().finally(() => navigate("/login", { replace: true }))
	}

	return (
		<div className="admin">
			<header className="admin-bar">
				<div className="brand">
					<LogoMark />
					<span className="brand-name">Mod Picker</span>
					<span className="role-tag">Админ-панель</span>
				</div>
				<div className="admin-actions">
					<ThemeToggle />
					<div className="who">
						<div className="whoami-avatar">
							<UserIcon />
						</div>
						<span className="whoami-name">Администратор</span>
					</div>
					<button type="button" className="out" onClick={logout}>
						<LogoutIcon size={18} />
						<span>Выйти</span>
					</button>
				</div>
			</header>

			<main className="admin-main">
				<div className="admin-head">
					<h1>Админ-панель</h1>
					<p>Числовые показатели использования приложения. Данные обновляются автоматически.</p>
					{updatedAt && (
						<p className="admin-updated">
							Обновлено в {updatedAt.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
						</p>
					)}
				</div>

				<div className="metric-row">
					<section className="card metric-main" aria-labelledby="m1">
						<div className="metric-title">
							<div className="metric-icon">
								<SearchIcon size={24} />
							</div>
							<h2 id="m1">Поисковых запросов пользователя</h2>
						</div>

						{stats.state === "ready" && (
							<div className="metric-value-wrap">
								<div className="metric-value">{formatCount(stats.data.requests)}</div>
								<div className="metric-note">Каждая отправка текста на поиск, независимо от исхода</div>
							</div>
						)}
						{stats.state === "loading" && (
							<div role="status" className="metric-loading">
								<div className="skel-block" />
								<div>Загружаем данные…</div>
							</div>
						)}
						{stats.state === "error" && (
							<div role="alert" className="metric-error">
								<AlertIcon size={22} />
								<span>Не удалось получить данные. Попробуйте обновить страницу</span>
							</div>
						)}
					</section>

					<aside className="card metric-side" aria-labelledby="m2">
						<h2 id="m2">Что считается запросом</h2>
						<ul className="rules-list">
							<li>
								<span className="ok">
									<CheckIcon />
								</span>
								<span>Отправка текста на поиск: с результатами, с пустой выдачей или с ошибкой</span>
							</li>
							<li>
								<span className="ok">
									<CheckIcon />
								</span>
								<span>Запрос из готового примера считается как обычный</span>
							</li>
							<li>
								<span className="no">
									<CrossIcon />
								</span>
								<span>Пустой запрос и запрос, не прошедший проверку, не считаются</span>
							</li>
						</ul>
					</aside>
				</div>

				{stats.state === "ready" && <ExtraMetrics data={stats.data} />}

				{stats.state === "loading" && (
					<section className="metrics-extra" aria-hidden="true">
						{["Число входов", "Доля запросов без результатов", "Запросы по дням"].map((title) => (
							<div className="card stat-card" key={title}>
								<span className="stat-title">{title}</span>
								<div className="skel-block" />
							</div>
						))}
					</section>
				)}
			</main>
		</div>
	)
}

function ExtraMetrics({ data }: { data: StatsResponse }) {
	const maxDay = Math.max(1, ...data.byDay.map((d) => d.count))
	return (
		<section className="metrics-extra" aria-label="Другие показатели">
			<article className="card stat-card" aria-labelledby="m4">
				<div className="stat-head">
					<div className="stat-icon">
						<UserIcon size={20} />
					</div>
					<h2 id="m4" className="stat-title">
						Число входов
					</h2>
				</div>
				<div className="stat-value">{formatCount(data.logins)}</div>
				<div className="stat-note">Успешные входы за всё время</div>
			</article>

			<article className="card stat-card" aria-labelledby="m5">
				<div className="stat-head">
					<div className="stat-icon">
						<CrossIcon size={20} />
					</div>
					<h2 id="m5" className="stat-title">
						Доля запросов без результатов
					</h2>
				</div>
				<div className="stat-value">{formatPercent(data.noResults, data.requests)}</div>
				<div className="stat-note">
					{formatCount(data.noResults)} из {formatCount(data.requests)} запросов
				</div>
			</article>

			<article className="card stat-card days" aria-labelledby="m6">
				<div className="stat-head">
					<div className="stat-icon">
						<ChatIcon size={20} />
					</div>
					<h2 id="m6" className="stat-title">
						Запросы по дням
					</h2>
				</div>
				{data.byDay.length === 0 ? (
					<p className="stat-note">Пока нет данных</p>
				) : (
					<div className="day-chart">
						{data.byDay.map((day) => {
							const width = day.count === 0 ? 0 : Math.max(4, Math.round((day.count / maxDay) * 100))
							return (
								<div className="day-row" key={day.date}>
									<span className="day-name">{formatDay(day.date)}</span>
									<span className="day-track">
										<span className="day-fill" style={{ width: `${width}%` }} />
									</span>
									<span className="day-count">{formatCount(day.count)}</span>
								</div>
							)
						})}
					</div>
				)}
			</article>
		</section>
	)
}
