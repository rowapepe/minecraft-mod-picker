import { useState } from "react"
import { applyTheme, currentTheme, saveTheme, type Theme } from "../library/theme"
import { MoonIcon, SunIcon } from "./Icons"

/** Переключатель темы на всех экранах (RULE-UI-12). */
export function ThemeToggle({ className = "" }: { className?: string }) {
	const [theme, setTheme] = useState<Theme>(currentTheme)
	const dark = theme === "dark"
	const label = dark ? "Включить светлую тему" : "Включить тёмную тему"

	const toggle = () => {
		const next: Theme = dark ? "light" : "dark"
		setTheme(next)
		applyTheme(next)
		saveTheme(next)
	}

	return (
		<button
			type="button"
			className={`ibtn theme-toggle ${className}`.trim()}
			onClick={toggle}
			aria-label={label}
			title={label}
		>
			{dark ? <SunIcon size={24} /> : <MoonIcon size={24} />}
		</button>
	)
}
