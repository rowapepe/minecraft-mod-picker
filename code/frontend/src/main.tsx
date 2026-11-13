import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter } from "react-router-dom"
import "@fontsource-variable/inter"
import "./styles/tokens.css"
import "./styles/app.css"
import { App } from "./App"
import { initTheme } from "./library/theme"

// Тема применяется до отрисовки, чтобы не было вспышки другого цвета (RULE-UI-12).
initTheme()

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<BrowserRouter>
			<App />
		</BrowserRouter>
	</StrictMode>
)
