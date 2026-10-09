import { useLayoutEffect, useRef, type KeyboardEvent } from "react"
import { MAX_QUERY_LENGTH } from "../library/query"
import { SendIcon } from "./Icons"

interface Props {
	value: string
	loading: boolean
	hint: boolean
	onChange: (value: string) => void
	onSubmit: () => void
}

/** Форма запроса (04, раздел 3.6): растущее поле, счётчик, кнопка поиска. */
export function Composer({ value, loading, hint, onChange, onSubmit }: Props) {
	const ref = useRef<HTMLTextAreaElement>(null)

	// Поле растёт по мере ввода, до 168 px.
	useLayoutEffect(() => {
		const el = ref.current
		if (!el) return
		el.style.height = "auto"
		el.style.height = `${Math.min(el.scrollHeight, 168)}px`
	}, [value])

	const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
		// Enter, Ctrl+Enter и Cmd+Enter отправляют, Shift+Enter переносит строку (RULE-UI-10).
		if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
			e.preventDefault()
			onSubmit()
		}
	}

	return (
		<>
			<div className="box">
				<label className="sr-only" htmlFor="query">
					Опишите задачу
				</label>
				<textarea
					id="query"
					ref={ref}
					className="ta"
					rows={1}
					maxLength={MAX_QUERY_LENGTH}
					placeholder="Например: хочу автоматизировать ферму и не получить лагов"
					value={value}
					onChange={(e) => onChange(e.target.value)}
					onKeyDown={onKeyDown}
				/>
				<div className="box-row">
					<div className="box-info">
						<span className="counter">
							{value.length} / {MAX_QUERY_LENGTH}
						</span>
						{hint && (
							<span role="alert" className="hint">
								Опишите задачу, чтобы начать поиск
							</span>
						)}
					</div>
					<button type="button" className="send" onClick={onSubmit} disabled={loading} aria-label="Найти моды" title="Найти моды">
						<SendIcon />
					</button>
				</div>
			</div>
			<div className="keys-hint">Enter — найти · Shift+Enter — новая строка</div>
		</>
	)
}
