import { useEffect, useState, type ReactNode } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { api, type Role } from './api';
import { AdminPage } from './pages/AdminPage';
import { LoginPage } from './pages/LoginPage';
import { SearchPage } from './pages/SearchPage';

const HOME: Record<Role, string> = { user: '/search', admin: '/admin' };

type Session = { checked: false } | { checked: true; role: Role | null };

/**
 * Защита экранов (RULE-AUTH-05, 04 раздел 9). Роль спрашивается у сервера при каждом переходе;
 * пока ответа нет, содержимое не показывается (GWT-18, GWT-19, GWT-20).
 * need: роль, которой нужен экран, либо 'guest' для экрана входа.
 */
function Guard({ need, children }: { need: Role | 'guest'; children: ReactNode }) {
  const location = useLocation();
  const [session, setSession] = useState<Session>({ checked: false });

  useEffect(() => {
    let alive = true;
    setSession({ checked: false });
    api
      .me()
      .then((role) => alive && setSession({ checked: true, role }))
      .catch(() => alive && setSession({ checked: true, role: null }));
    return () => {
      alive = false;
    };
  }, [location.pathname]);

  if (!session.checked) return null;
  const { role } = session;
  if (need === 'guest') return role ? <Navigate to={HOME[role]} replace /> : <>{children}</>;
  if (!role) return <Navigate to="/login" replace />;
  if (role !== need) return <Navigate to={HOME[role]} replace />;
  return <>{children}</>;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<Guard need="guest"><LoginPage /></Guard>} />
      <Route path="/search" element={<Guard need="user"><SearchPage /></Guard>} />
      <Route path="/admin" element={<Guard need="admin"><AdminPage /></Guard>} />
      <Route path="*" element={<Navigate to="/search" replace />} />
    </Routes>
  );
}
