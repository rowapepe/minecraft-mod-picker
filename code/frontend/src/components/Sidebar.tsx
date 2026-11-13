import { useEffect, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { FallenSkeleton } from "../mascot/Mascot"
import { shortTitle } from "../library/query"
import { LogoMark } from "./Logo"
import { ChatIcon, LogoutIcon, PanelIcon, PlusIcon, TrashIcon, UserIcon } from "./Icons"

export interface SidebarItem {
	id: number
	title: string
}

interface Props {
	open: boolean
	items: SidebarItem[]
	activeId: number | null
	onToggle: () => void
	onNew: () => void
	onPick: (id: number) => void
	onDelete: (id: number) => void
	onLogout: () => void
}

/** Боковая панель: раскрытая (280 px) или узкая полоса значков (RULE-UI-06, RULE-UI-07). */
export function Sidebar({ open, items, activeId, onToggle, onNew, onPick, onDelete, onLogout }: Props) {
	const [confirmId, setConfirmId] = useState<number | null>(null)
	const triggerRef = useRef<HTMLElement | null>(null)
	const confirmItem = items.find((it) => it.id === confirmId) ?? null

	const openConfirm = (id: number, trigger: HTMLElement) => {
		triggerRef.current = trigger
		setConfirmId(id)
	}

	const cancelConfirm = () => {
		const trigger = triggerRef.current
		triggerRef.current = null
		setConfirmId(null)
		requestAnimationFrame(() => {
			if (trigger?.isConnected) trigger.focus()
		})
	}

	const confirmDelete = (id: number) => {
		triggerRef.current = null
		onDelete(id)
		setConfirmId(null)
	}

	return (
		<>
			<aside className={`sb ${open ? "open" : "closed"}`} aria-label="Боковая панель">
				{open ? (
					<div className="sb-full">
						<div className="sb-top">
							<div className="brand">
								<LogoMark />
								<span className="brand-name">Mod Picker</span>
							</div>
							<button type="button" className="ibtn" onClick={onToggle} aria-label="Свернуть панель" title="Свернуть панель">
								<PanelIcon />
							</button>
						</div>

						<button type="button" className="newbtn" onClick={onNew}>
							<PlusIcon />
							<span>Новый поиск</span>
						</button>

						<div className="sb-list-wrap">
							<div className="sb-label">Чаты в этой сессии</div>
							<div className="sb-list scroll">
								{items.length === 0 ? (
									<FallenSkeleton />
								) : (
									items.map((it) => (
										<div className="thread-item" key={it.id}>
											<div className={`thread-row ${it.id === activeId ? "on" : ""}`}>
												<button
													type="button"
													className={`thread ${it.id === activeId ? "on" : ""}`}
													onClick={() => onPick(it.id)}
													aria-current={it.id === activeId ? "true" : undefined}
													title={it.title}
												>
													<ChatIcon />
													<span>{shortTitle(it.title)}</span>
												</button>
												<button
													type="button"
													className="thread-del"
													onClick={(event) => openConfirm(it.id, event.currentTarget)}
													aria-label={`Удалить чат: ${shortTitle(it.title)}`}
													title="Удалить чат"
												>
													<TrashIcon size={16} />
												</button>
											</div>
										</div>
									))
								)}
							</div>
						</div>

						<div className="sb-bottom">
							<div className="whoami">
								<div className="whoami-avatar">
									<UserIcon />
								</div>
								<div className="whoami-text">
									<span className="whoami-name">Пользователь</span>
									<span className="whoami-sub">Поиск модов</span>
								</div>
							</div>
							<button type="button" className="exit" onClick={onLogout}>
								<LogoutIcon />
								<span>Выйти</span>
							</button>
						</div>
					</div>
				) : (
					<div className="sb-rail">
						<button type="button" className="ibtn" onClick={onToggle} aria-label="Развернуть панель" title="Развернуть панель">
							<PanelIcon />
						</button>
						<button type="button" className="ibtn accent-btn" onClick={onNew} aria-label="Новый поиск" title="Новый поиск">
							<PlusIcon />
						</button>
						<div className="grow" />
						<button type="button" className="ibtn" onClick={onLogout} aria-label="Выйти" title="Выйти">
							<LogoutIcon />
						</button>
					</div>
				)}
			</aside>
			<div className={`scrim ${open ? "open" : ""}`} onClick={onToggle} aria-hidden="true" />
			{confirmItem && (
				<ConfirmDeleteDialog
					title={confirmItem.title}
					onCancel={cancelConfirm}
					onConfirm={() => confirmDelete(confirmItem.id)}
				/>
			)}
		</>
	)
}

interface ConfirmDeleteProps {
	title: string
	onCancel: () => void
	onConfirm: () => void
}

/** Подтверждение удаления: затемнение экрана и окно по центру (RULE-UI-13). */
function ConfirmDeleteDialog({ title, onCancel, onConfirm }: ConfirmDeleteProps) {
	const dialogRef = useRef<HTMLDivElement>(null)
	const cancelRef = useRef<HTMLButtonElement>(null)

	useEffect(() => {
		cancelRef.current?.focus()
		const onKey = (event: KeyboardEvent) => {
			if (event.key === "Escape") {
				event.preventDefault()
				onCancel()
				return
			}
			if (event.key !== "Tab") return
			const nodes = dialogRef.current?.querySelectorAll<HTMLElement>("button")
			if (!nodes || nodes.length === 0) return
			const first = nodes[0]
			const last = nodes[nodes.length - 1]
			if (event.shiftKey && document.activeElement === first) {
				event.preventDefault()
				last.focus()
			} else if (!event.shiftKey && document.activeElement === last) {
				event.preventDefault()
				first.focus()
			}
		}
		document.addEventListener("keydown", onKey)
		return () => document.removeEventListener("keydown", onKey)
	}, [onCancel])

	return createPortal(
		<div className="modal-scrim" onMouseDown={(event) => event.target === event.currentTarget && onCancel()}>
			<div
				ref={dialogRef}
				className="confirm-dialog"
				role="alertdialog"
				aria-modal="true"
				aria-labelledby="confirm-delete-title"
				aria-describedby="confirm-delete-text"
			>
				<div className="confirm-icon" aria-hidden="true">
					<TrashIcon size={22} />
				</div>
				<h2 id="confirm-delete-title" className="confirm-title">
					Удалить чат?
				</h2>
				<p id="confirm-delete-text" className="confirm-text">
					Чат «{shortTitle(title)}» и все его сообщения будут удалены. Это действие нельзя отменить.
				</p>
				<div className="confirm-actions">
					<button ref={cancelRef} type="button" className="confirm-btn" onClick={onCancel}>
						Отмена
					</button>
					<button type="button" className="confirm-btn danger" onClick={onConfirm}>
						Удалить
					</button>
				</div>
			</div>
		</div>,
		document.body
	)
}
