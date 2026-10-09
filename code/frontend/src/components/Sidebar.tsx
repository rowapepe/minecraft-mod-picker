import { FallenSkeleton } from '../mascot/Mascot';
import { shortTitle } from '../lib/query';
import { LogoMark } from './Logo';
import { ChatIcon, LogoutIcon, PanelIcon, PlusIcon, UserIcon } from './Icons';

export interface SidebarItem {
  id: number;
  query: string;
}

interface Props {
  open: boolean;
  items: SidebarItem[];
  activeId: number | null;
  onToggle: () => void;
  onNew: () => void;
  onPick: (id: number) => void;
  onLogout: () => void;
}

/** Боковая панель: раскрытая (280 px) или узкая полоса значков (RULE-UI-06, RULE-UI-07). */
export function Sidebar({ open, items, activeId, onToggle, onNew, onPick, onLogout }: Props) {
  return (
    <>
      <aside className={`sb ${open ? 'open' : 'closed'}`} aria-label="Боковая панель">
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
              <div className="sb-label">Запросы в этой сессии</div>
              <div className="sb-list scroll">
                {items.length === 0 ? (
                  <FallenSkeleton />
                ) : (
                  items.map((it) => (
                    <button
                      type="button"
                      key={it.id}
                      className={`thread ${it.id === activeId ? 'on' : ''}`}
                      onClick={() => onPick(it.id)}
                      aria-current={it.id === activeId ? 'true' : undefined}
                      title={it.query}
                    >
                      <ChatIcon />
                      <span>{shortTitle(it.query)}</span>
                    </button>
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
      <div className={`scrim ${open ? 'open' : ''}`} onClick={onToggle} aria-hidden="true" />
    </>
  );
}
