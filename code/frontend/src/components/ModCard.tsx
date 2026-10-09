import type { Mod } from '../api';
import { ExternalIcon } from './Icons';

const TILE_COLORS = ['#8ee3b0', '#ffc875', '#9fc4ff', '#c9a8ff', '#ff9d8a', '#a6e57a', '#ffb27a', '#8ec9ff'];

function tileColor(slug: string): string {
  let h = 0;
  for (const ch of slug) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return TILE_COLORS[h % TILE_COLORS.length];
}

/** Карточка мода (RULE-UI-04): название, описание, до пяти категорий, ссылка в новой вкладке. */
export function ModCard({ mod }: { mod: Mod }) {
  const initial = mod.title.replace(/[^\p{L}\p{N}]/gu, '').charAt(0).toUpperCase();
  return (
    <article className="mod-card">
      <div className="mod-tile" style={{ background: tileColor(mod.slug) }} aria-hidden="true">
        {initial}
      </div>
      <div className="mod-body">
        <h3 className="mod-title">{mod.title}</h3>
        <p className="mod-desc">{mod.description}</p>
        <div className="chips">
          {mod.categories.slice(0, 5).map((c) => (
            <span className="chip" key={c}>
              {c}
            </span>
          ))}
        </div>
      </div>
      <a className="open-link" href={mod.url} target="_blank" rel="noopener noreferrer">
        <span>Открыть на Modrinth</span>
        <ExternalIcon />
      </a>
    </article>
  );
}
