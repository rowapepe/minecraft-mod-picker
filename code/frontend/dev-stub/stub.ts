/**
 * Заглушка API для разработки интерфейса без бэкенда (D-26).
 * Подключается только в `npm run dev` без API_TARGET и в сборку не входит.
 * Повторяет контракт из docs/Tech/04-api-and-access.md.
 *
 * Особые запросы для проверки состояний: «!пусто», «!ошибка», «!безответа».
 */
import { randomBytes } from 'node:crypto';
import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import type { IncomingMessage, ServerResponse } from 'node:http';
import { dirname, resolve } from 'node:path';
import type { Plugin } from 'vite';
import { detectCostume } from '../src/mascot/detect';
import type { CostumeId } from '../src/mascot/costumes';

type Role = 'user' | 'admin';
interface StubMod { slug: string; title: string; description: string; categories: string[] }

/** Метрики, которые заглушка сохраняет между перезапусками (D-15, RULE-ADM-03). */
interface StoredAnalytics {
  requests: number;
  logins: number;
  noResults: number;
  byDay: Record<string, number>;
}

const emptyAnalytics = (): StoredAnalytics => ({ requests: 0, logins: 0, noResults: 0, byDay: {} });

const isCount = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0;

function readAnalytics(file: string): StoredAnalytics {
  try {
    const raw = JSON.parse(readFileSync(file, 'utf8')) as Partial<StoredAnalytics>;
    const byDay: Record<string, number> = {};
    if (raw.byDay && typeof raw.byDay === 'object') {
      for (const [date, count] of Object.entries(raw.byDay)) {
        if (/^\d{4}-\d{2}-\d{2}$/.test(date) && isCount(count)) byDay[date] = Math.floor(count);
      }
    }
    return {
      requests: isCount(raw.requests) ? Math.floor(raw.requests) : 0,
      logins: isCount(raw.logins) ? Math.floor(raw.logins) : 0,
      noResults: isCount(raw.noResults) ? Math.floor(raw.noResults) : 0,
      byDay,
    };
  } catch {
    return emptyAnalytics();
  }
}

const SETS: Record<CostumeId, { answer: string; mods: StubMod[] }> = {
  base: {
    answer: 'Подобрал универсальные моды-помощники, которые пригодятся почти в любой сборке.',
    mods: [
      { slug: 'jade', title: 'Jade', description: 'Показывает подсказку о блоке или существе под прицелом.', categories: ['Утилиты', 'Интерфейс'] },
      { slug: 'jei', title: 'Just Enough Items', description: 'Просмотр предметов и рецептов прямо в инвентаре.', categories: ['Утилиты', 'Рецепты'] },
      { slug: 'xaeros-minimap', title: "Xaero's Minimap", description: 'Миникарта с метками и отображением окрестностей.', categories: ['Карта', 'Интерфейс'] },
      { slug: 'appleskin', title: 'AppleSkin', description: 'Показывает насыщение и восстановление от еды.', categories: ['Утилиты', 'Еда'] },
    ],
  },
  miner: {
    answer: 'Для новой генерации мира и приключений под землёй подойдут эти моды: они меняют ландшафт, пещеры и шахты.',
    mods: [
      { slug: 'terralith', title: 'Terralith', description: 'Новые биомы и обновлённая генерация ландшафта.', categories: ['Генерация мира', 'Биомы'] },
      { slug: 'yungs-better-mineshafts', title: "YUNG's Better Mineshafts", description: 'Переработанные заброшенные шахты с новыми комнатами.', categories: ['Генерация мира', 'Приключения'] },
      { slug: 'tectonic', title: 'Tectonic', description: 'Высокие горы и глубокие впадины в рельефе мира.', categories: ['Генерация мира', 'Ландшафт'] },
      { slug: 'alexs-caves', title: "Alex's Caves", description: 'Новые пещерные биомы с существами и находками.', categories: ['Генерация мира', 'Приключения'] },
    ],
  },
  wizard: {
    answer: 'Для игры с заклинаниями подойдут моды, где магия построена на разных механиках: от рун до книг заклинаний.',
    mods: [
      { slug: 'ars-nouveau', title: 'Ars Nouveau', description: 'Магия на основе глифов, из которых собираются свои заклинания.', categories: ['Магия', 'Приключения'] },
      { slug: 'botania', title: 'Botania', description: 'Магия, которая использует цветы и ману.', categories: ['Магия', 'Технологии'] },
      { slug: 'irons-spells-n-spellbooks', title: "Iron's Spells 'n Spellbooks", description: 'Школы магии, книги заклинаний и новые боевые умения.', categories: ['Магия', 'Боевая система'] },
      { slug: 'occultism', title: 'Occultism', description: 'Духи и ритуалы для добычи ресурсов и автоматизации.', categories: ['Магия', 'Технологии'] },
    ],
  },
  shades: {
    answer: 'Для красивой картинки нужна связка: один мод ускоряет отрисовку, другой подключает шейдеры, остальные расширяют дальность и освещение.',
    mods: [
      { slug: 'iris', title: 'Iris Shaders', description: 'Загрузка шейдерпаков с совместимостью с Sodium.', categories: ['Графика', 'Шейдеры'] },
      { slug: 'sodium', title: 'Sodium', description: 'Современный движок отрисовки, который повышает FPS.', categories: ['Графика', 'Оптимизация'] },
      { slug: 'distant-horizons', title: 'Distant Horizons', description: 'Показывает далёкие участки мира с упрощённой детализацией.', categories: ['Графика', 'Генерация мира'] },
      { slug: 'lambdynamiclights', title: 'LambDynamicLights', description: 'Динамическое освещение от предметов в руках и существ.', categories: ['Графика', 'Освещение'] },
    ],
  },
  knight: {
    answer: 'Для более интересных сражений подойдут моды, которые меняют ближний бой и добавляют сильных противников.',
    mods: [
      { slug: 'better-combat', title: 'Better Combat', description: 'Новая система ближнего боя с анимациями ударов.', categories: ['Боевая система', 'Анимации'] },
      { slug: 'epic-fight', title: 'Epic Fight', description: 'Новые боевые приёмы, анимации и стиль сражений.', categories: ['Боевая система', 'Приключения'] },
      { slug: 'bosses-of-mass-destruction', title: 'Bosses of Mass Destruction', description: 'Крупные боссы для настоящих испытаний.', categories: ['Мобы', 'Приключения'] },
      { slug: 'simply-swords', title: 'Simply Swords', description: 'Новые мечи с уникальными умениями.', categories: ['Боевая система', 'Оружие'] },
    ],
  },
  builder: {
    answer: 'Для строительства и порядка на базе подойдут моды с декоративными блоками, удобным хранением и чертежами.',
    mods: [
      { slug: 'sophisticated-storage', title: 'Sophisticated Storage', description: 'Улучшаемые сундуки и бочки с удобным интерфейсом.', categories: ['Хранение', 'Утилиты'] },
      { slug: 'chipped', title: 'Chipped', description: 'Много вариантов декоративных блоков для оформления построек.', categories: ['Декор', 'Строительство'] },
      { slug: 'litematica', title: 'Litematica', description: 'Схемы построек, которые показываются прямо в мире.', categories: ['Строительство', 'Утилиты'] },
      { slug: 'framedblocks', title: 'FramedBlocks', description: 'Каркасные блоки любой формы для точных построек.', categories: ['Строительство', 'Декор'] },
    ],
  },
  farmer: {
    answer: 'Для фермы с автоматизацией подойдут моды с новыми культурами, едой и механизмами, которые берут рутину на себя.',
    mods: [
      { slug: 'farmers-delight', title: "Farmer's Delight", description: 'Новые культуры, кулинария и кухонная утварь.', categories: ['Еда', 'Фермерство'] },
      { slug: 'croptopia', title: 'Croptopia', description: 'Множество новых растений и блюд из них.', categories: ['Еда', 'Фермерство'] },
      { slug: 'create', title: 'Create', description: 'Механизмы и конвейеры для автоматизации работ.', categories: ['Технологии', 'Автоматизация'] },
      { slug: 'botany-pots', title: 'Botany Pots', description: 'Горшки для выращивания культур в одном блоке.', categories: ['Фермерство', 'Утилиты'] },
    ],
  },
  racer: {
    answer: 'Для слабого компьютера подойдут эти моды: каждый берёт на себя свою часть нагрузки.',
    mods: [
      { slug: 'sodium', title: 'Sodium', description: 'Современный движок отрисовки, который повышает FPS.', categories: ['Оптимизация', 'Графика'] },
      { slug: 'lithium', title: 'Lithium', description: 'Оптимизация игровой логики без изменения геймплея.', categories: ['Оптимизация', 'Сервер'] },
      { slug: 'ferritecore', title: 'FerriteCore', description: 'Снижает расход оперативной памяти.', categories: ['Оптимизация', 'Память'] },
      { slug: 'entityculling', title: 'Entity Culling', description: 'Не отрисовывает невидимые сущности и блоки, повышая FPS.', categories: ['Оптимизация', 'Графика'] },
    ],
  },
};

function readBody(req: IncomingMessage): Promise<Record<string, unknown>> {
  return new Promise((resolve) => {
    let raw = '';
    req.on('data', (c) => (raw += c));
    req.on('end', () => {
      try {
        resolve(raw ? JSON.parse(raw) : {});
      } catch {
        resolve({});
      }
    });
  });
}

/** Ключ дня и последние семь дней для аналитики (RULE-ADM-05). */
function dayKey(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function lastDays(byDay: Map<string, number>, size = 7): Array<{ date: string; count: number }> {
  const days: Array<{ date: string; count: number }> = [];
  for (let offset = size - 1; offset >= 0; offset -= 1) {
    const date = new Date();
    date.setDate(date.getDate() - offset);
    const key = dayKey(date);
    days.push({ date: key, count: byDay.get(key) ?? 0 });
  }
  return days;
}

function send(res: ServerResponse, status: number, body?: unknown, headers: Record<string, string> = {}) {
  res.statusCode = status;
  if (body !== undefined) res.setHeader('Content-Type', 'application/json; charset=utf-8');
  for (const [k, v] of Object.entries(headers)) res.setHeader(k, v);
  res.end(body === undefined ? undefined : JSON.stringify(body));
}

export function apiStub(env: Record<string, string>): Plugin {
  const accounts: Array<{ login: string; password: string; role: Role }> = [
    { login: env.USER_LOGIN, password: env.USER_PASSWORD, role: 'user' as const },
    { login: env.ADMIN_LOGIN, password: env.ADMIN_PASSWORD, role: 'admin' as const },
  ].filter((a) => a.login && a.password);

  const sessions = new Map<string, Role>();

  const roleOf = (req: IncomingMessage): Role | null => {
    const m = /(?:^|;\s*)session=([^;]+)/.exec(req.headers.cookie ?? '');
    return (m && sessions.get(m[1])) || null;
  };

  return {
    name: 'dev-api-stub',
    apply: 'serve',
    configureServer(server) {
      if (accounts.length < 2) {
        server.config.logger.warn(
          '[dev-stub] USER_LOGIN/USER_PASSWORD/ADMIN_LOGIN/ADMIN_PASSWORD не заданы в .env: вход невозможен',
        );
      }

      // Файл живёт вне Git (.dev-stub/): запросы и входы переживают перезапуск dev-сервера.
      const analyticsFile = resolve(server.config.root, '.dev-stub/analytics.json');
      const saved = readAnalytics(analyticsFile);
      let requests = saved.requests;
      let logins = saved.logins;
      let noResults = saved.noResults;
      const byDay = new Map<string, number>(Object.entries(saved.byDay));

      const saveAnalytics = () => {
        try {
          mkdirSync(dirname(analyticsFile), { recursive: true });
          const tmp = `${analyticsFile}.tmp`;
          const body: StoredAnalytics = { requests, logins, noResults, byDay: Object.fromEntries(byDay) };
          writeFileSync(tmp, JSON.stringify(body), 'utf8');
          renameSync(tmp, analyticsFile);
        } catch (error) {
          server.config.logger.warn(`[dev-stub] не удалось сохранить аналитику: ${String(error)}`);
        }
      };

      server.middlewares.use(async (req, res, next) => {
        const url = (req.url ?? '').split('?')[0];
        if (!url.startsWith('/api/')) return next();
        const role = roleOf(req);

        if (url === '/api/auth/login' && req.method === 'POST') {
          const { login, password } = await readBody(req);
          const acc = accounts.find((a) => a.login === login && a.password === password);
          if (!acc) return send(res, 401, { detail: 'invalid' });
          logins += 1; // RULE-ADM-04: только успешный вход
          const token = randomBytes(24).toString('hex');
          sessions.set(token, acc.role);
          saveAnalytics();
          return send(res, 200, { role: acc.role }, { 'Set-Cookie': `session=${token}; HttpOnly; Path=/; SameSite=Lax` });
        }
        if (url === '/api/auth/logout' && req.method === 'POST') {
          const m = /(?:^|;\s*)session=([^;]+)/.exec(req.headers.cookie ?? '');
          if (m) sessions.delete(m[1]);
          return send(res, 204, undefined, { 'Set-Cookie': 'session=; HttpOnly; Path=/; Max-Age=0' });
        }
        if (url === '/api/auth/me' && req.method === 'GET') {
          return role ? send(res, 200, { role }) : send(res, 401, { detail: 'no session' });
        }
        if (url === '/api/search' && req.method === 'POST') {
          if (!role) return send(res, 401, { detail: 'no session' });
          if (role !== 'user') return send(res, 403, { detail: 'forbidden' });
          const query = String((await readBody(req)).query ?? '');
          if (!query.trim() || query.length > 500) return send(res, 400, { detail: 'bad query' });
          requests += 1; // RULE-ADM-02: считается независимо от исхода
          const today = dayKey(); // RULE-ADM-05
          byDay.set(today, (byDay.get(today) ?? 0) + 1);
          saveAnalytics();
          await new Promise((r) => setTimeout(r, 1200));
          const q = query.trim().toLowerCase();
          if (q === '!ошибка') return send(res, 500, { detail: 'Не удалось выполнить поиск' });
          if (q === '!пусто') {
            noResults += 1; // RULE-ADM-06
            saveAnalytics();
            return send(res, 200, { mods: [], answer: null });
          }
          const set = SETS[detectCostume(query).id];
          const mods = set.mods.map((m) => ({ ...m, url: `https://modrinth.com/mod/${m.slug}` }));
          return send(res, 200, { mods, answer: q === '!безответа' ? null : set.answer });
        }
        if (url === '/api/admin/stats' && req.method === 'GET') {
          if (!role) return send(res, 401, { detail: 'no session' });
          if (role !== 'admin') return send(res, 403, { detail: 'forbidden' });
          return send(res, 200, { requests, logins, byDay: lastDays(byDay), noResults });
        }
        return send(res, 404, { detail: 'not found' });
      });
    },
  };
}
