import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { AlertIcon, SpinnerIcon } from '../components/Icons';
import { LogoMark } from '../components/Logo';
import { BASE } from '../mascot/costumes';
import { Zombie } from '../mascot/Mascot';

type Message = null | 'empty' | 'wrong';

const TEXT: Record<Exclude<Message, null>, string> = {
  empty: 'Введите логин и пароль',
  wrong: 'Неверный логин или пароль',
};

const PREVIEW_MODS = ['Sodium', 'Lithium', 'FerriteCore'];

/** Экран входа (04, раздел 7). Регистрации и восстановления пароля нет (RULE-AUTH-01). */
export function LoginPage() {
  const navigate = useNavigate();
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<Message>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    document.title = 'Вход';
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (checking) return;
    if (!login.trim() || !password) {
      setMessage('empty'); // GWT-17: данные не проверяются
      return;
    }
    setChecking(true);
    try {
      const role = await api.login(login, password);
      navigate(role === 'admin' ? '/admin' : '/search', { replace: true });
    } catch {
      setMessage('wrong'); // GWT-16: логин остаётся, пароль очищается
      setPassword('');
      setChecking(false);
    }
  };

  const invalid = message !== null;

  return (
    <div className="login">
      <section className="login-hero grid-bg">
        <div className="brand">
          <LogoMark size={36} />
          <span className="brand-name big">Minecraft Mod Picker</span>
        </div>

        <div className="hero-copy">
          <h1 className="hero-title">Расскажите, что хотите делать в игре. Мы подберём моды.</h1>
          <p className="hero-sub">Поиск по описаниям модов с Modrinth и объяснение, почему подошли именно эти моды.</p>
        </div>

        <div className="hero-preview" aria-hidden="true">
          <div className="pv-user">Хочу улучшить производительность на слабом компьютере</div>
          <div className="pv-answer">
            <div className="avatar small" />
            <div className="pv-body">
              <div className="pv-text">Для слабого компьютера подойдут три мода, каждый берёт на себя свою часть нагрузки.</div>
              <div className="chips">
                {PREVIEW_MODS.map((m) => (
                  <span className="pv-chip" key={m}>{m}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="login-side">
        <div className="login-card-wrap">
          <Zombie costume={BASE} className="login-zombie" />
          <form className="login-card" onSubmit={submit} noValidate>
            <div className="login-head">
              <h2>Вход</h2>
              <p>Войдите, чтобы подобрать моды</p>
            </div>

            <div className="field-group">
              <label htmlFor="login">Логин</label>
              <input
                id="login"
                className="field"
                type="text"
                autoComplete="username"
                value={login}
                aria-invalid={invalid}
                onChange={(e) => {
                  setLogin(e.target.value);
                  setMessage(null);
                }}
              />
            </div>

            <div className="field-group">
              <label htmlFor="password">Пароль</label>
              <input
                id="password"
                className="field"
                type="password"
                autoComplete="current-password"
                value={password}
                aria-invalid={invalid}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setMessage(null);
                }}
              />
            </div>

            <div className="msg-slot">
              {message && (
                <div role="alert" className="form-error">
                  <AlertIcon />
                  <span>{TEXT[message]}</span>
                </div>
              )}
            </div>

            <button type="submit" className="go" disabled={checking}>
              {checking && <SpinnerIcon />}
              <span>{checking ? 'Проверяем…' : 'Войти'}</span>
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
