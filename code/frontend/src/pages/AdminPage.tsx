import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "../api"
import { AlertIcon, CheckIcon, CrossIcon, LogoutIcon, SearchIcon, UserIcon } from "../components/Icons"
import { LogoMark } from "../components/Logo"
import { formatCount } from "../library/format"

type Stats = { state: "loading" } | { state: "error" } | { state: "ready"; requests: number }

const FUTURE = [
	{ title: "Запросы по дням", sub: "Динамика нагрузки" },
	{ title: "Число входов", sub: "Как часто заходят в приложение" },
	{ title: "Доля запросов без результатов", sub: "Где поиск не находит моды" }
]

/** Админ-панель (04, раздел 8): числовая аналитика (RULE-ADM-01). */
export function AdminPage() {
	const navigate = useNavigate()
	const [stats, setStats] = useState<Stats>({ state: "loading" })

	useEffect(() => {
		document.title = "Админ-панель"
		let alive = true
		api
			.stats()
			.then((r) => alive && setStats({ state: "ready", requests: r.requests }))
			.catch(() => alive && setStats({ state: "error" }))
		return () => {
			alive = false
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
					<p>Числовые показатели использования приложения. Новые значения появляются после обновления страницы.</p>
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
								<div className="metric-value">{formatCount(stats.requests)}</div>
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

				<section className="future" aria-labelledby="m3">
					<div className="future-head">
						<h2 id="m3">Возможные показатели</h2>
						<span className="pill">не утверждено</span>
					</div>
					<div className="future-grid">
						{FUTURE.map((f) => (
							<div className="future-card" key={f.title}>
								<span className="future-title">{f.title}</span>
								<span className="future-sub">{f.sub}</span>
							</div>
						))}
					</div>
				</section>
			</main>
		</div>
	)
}
