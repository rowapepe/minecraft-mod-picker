/** Тема интерфейса (RULE-UI-12): тёмная по умолчанию, светлая по выбору. */

export type Theme = "dark" | "light"

const STORAGE_KEY = "mod-picker-theme"

function isTheme(value: string | null): value is Theme {
	return value === "dark" || value === "light"
}

function readStored(): Theme | null {
	try {
		const value = localStorage.getItem(STORAGE_KEY)
		return isTheme(value) ? value : null
	} catch {
		return null
	}
}

function systemTheme(): Theme {
	return typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: light)").matches ? "light" : "dark"
}

/** Текущая тема: атрибут на <html>, сохранённый выбор или системная настройка. */
export function currentTheme(): Theme {
	const attr = document.documentElement.dataset.theme
	if (isTheme(attr ?? null)) return attr as Theme
	return readStored() ?? systemTheme()
}

export function applyTheme(theme: Theme): void {
	document.documentElement.dataset.theme = theme
}

export function saveTheme(theme: Theme): void {
	try {
		localStorage.setItem(STORAGE_KEY, theme)
	} catch {
		/* storage can be unavailable */
	}
}

/** Применяет тему до отрисовки, чтобы не было вспышки другого цвета. */
export function initTheme(): Theme {
	const theme = readStored() ?? systemTheme()
	applyTheme(theme)
	return theme
}
