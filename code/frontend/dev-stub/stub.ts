/**
 * Заглушка API для разработки интерфейса без бэкенда (GAP-13).
 * Подключается только в `npm run dev` без API_TARGET и в сборку не входит.
 * Повторяет контракт из docs/Tech/04-api-and-access.md.
 *
 * Особые запросы для проверки состояний: «!пусто», «!ошибка», «!безответа».
 */
import { randomBytes } from 'node:crypto';
import type { IncomingMessage, ServerResponse } from 'node:http';
import type { Plugin } from 'vite';
import { detectCostume } from '../src/mascot/detect';
import type { CostumeId } from '../src/mascot/costumes';

type Role = 'user' | 'admin';
interface StubMod { slug: string; title: string; description: string; categories: string[] }

const SETS: Record<CostumeId, { answer: string; mods: StubMod[] }> = {
  base: {
    answer: 'Подобрал универсальные моды-помощники, которые пригодятся почти в любой сборке.',
    mods: [
      { slug: 'jade', title: 'Jade', description: 'Показывает подсказку о блоке или существе под прицелом.', categories: ['Утилиты', 'Интерфейс'] },
      { slug: 'jei', title: 'Just Enough Items', description: 'Просмотр предметов и рецептов прямо в инвентаре.', categories: ['Утилиты', 'Рецепты'] },
      { slug: 'xaeros-minimap', title: "Xaero's Minimap", description: 'Миникарта с метками и отображением окрестностей.', categories: ['Карта', 'Интерфейс'] },
    ],
  },
  miner: {
    answer: 'Для новой генерации мира и приключений под землёй подойдут эти три мода: они меняют ландшафт, пещеры и шахты.',
    mods: [
      { slug: 'terralith', title: 'Terralith', description: 'Новые биомы и обновлённая генерация ландшафта.', categories: ['Генерация мира', 'Биомы'] },
      { slug: 'yungs-better-mineshafts', title: "YUNG's Better Mineshafts", description: 'Переработанные заброшенные шахты с новыми комнатами.', categories: ['Генерация мира', 'Приключения'] },
      { slug: 'tectonic', title: 'Tectonic', description: 'Высокие горы и глубокие впадины в рельефе мира.', categories: ['Генерация мира', 'Ландшафт'] },
    ],
  },
  wizard: {
    answer: 'Для игры с заклинаниями подойдут моды, где магия построена на разных механиках: от рун до книг заклинаний.',
    mods: [
      { slug: 'ars-nouveau', title: 'Ars Nouveau', description: 'Магия на основе глифов, из которых собираются свои заклинания.', categories: ['Магия', 'Приключения'] },
      { slug: 'botania', title: 'Botania', description: 'Магия, которая использует цветы и ману.', categories: ['Магия', 'Технологии'] },
      { slug: 'irons-spells-n-spellbooks', title: "Iron's Spells 'n Spellbooks", description: 'Школы магии, книги заклинаний и новые боевые умения.', categories: ['Магия', 'Боевая система'] },
    ],
  },
  shades: {
    answer: 'Для красивой картинки нужна связка: один мод ускоряет отрисовку, другой подключает шейдеры, третий расширяет дальность.',
    mods: [
      { slug: 'iris', title: 'Iris Shaders', description: 'Загрузка шейдерпаков с совместимостью с Sodium.', categories: ['Графика', 'Шейдеры'] },
      { slug: 'sodium', title: 'Sodium', description: 'Современный движок отрисовки, который повышает FPS.', categories: ['Графика', 'Оптимизация'] },
      { slug: 'distant-horizons', title: 'Distant Horizons', description: 'Показывает далёкие участки мира с упрощённой детализацией.', categories: ['Графика', 'Генерация мира'] },
    ],
  },
  knight: {
    answer: 'Для более интересных сражений подойдут моды, которые меняют ближний бой и добавляют сильных противников.',
    mods: [
      { slug: 'better-combat', title: 'Better Combat', description: 'Новая система ближнего боя с анимациями ударов.', categories: ['Боевая система', 'Анимации'] },
      { slug: 'epic-fight', title: 'Epic Fight', description: 'Новые боевые приёмы, анимации и стиль сражений.', categories: ['Боевая система', 'Приключения'] },
      { slug: 'bosses-of-mass-destruction', title: 'Bosses of Mass Destruction', description: 'Крупные боссы для настоящих испытаний.', categories: ['Мобы', 'Приключения'] },
    ],
  },
  builder: {
    answer: 'Для строительства и порядка на базе подойдут моды с декоративными блоками, удобным хранением и чертежами.',
    mods: [
      { slug: 'sophisticated-storage', title: 'Sophisticated Storage', description: 'Улучшаемые сундуки и бочки с удобным интерфейсом.', categories: ['Хранение', 'Утилиты'] },
      { slug: 'chipped', title: 'Chipped', description: 'Много вариантов декоративных блоков для оформления построек.', categories: ['Декор', 'Строительство'] },
      { slug: 'litematica', title: 'Litematica', description: 'Схемы построек, которые показываются прямо в мире.', categories: ['Строительство', 'Утилиты'] },
    ],
  },
  farmer: {
    answer: 'Для фермы с автоматизацией подойдут моды с новыми культурами, едой и механизмами, которые берут рутину на себя.',
    mods: [
      { slug: 'farmers-delight', title: "Farmer's Delight", description: 'Новые культуры, кулинария и кухонная утварь.', categories: ['Еда', 'Фермерство'] },
      { slug: 'croptopia', title: 'Croptopia', description: 'Множество новых растений и блюд из них.', categories: ['Еда', 'Фермерство'] },
      { slug: 'create', title: 'Create', description: 'Механизмы и конвейеры для автоматизации работ.', categories: ['Технологии', 'Автоматизация'] },
    ],
  },
  racer: {
    answer: 'Для слабого компьютера подойдут три мода, каждый из которых берёт на себя свою часть нагрузки.',
    mods: [
      { slug: 'sodium', title: 'Sodium', description: 'Современный движок отрисовки, который повышает FPS.', categories: ['Оптимизация', 'Графика'] },
      { slug: 'lithium', title: 'Lithium', description: 'Оптимизация игровой логики без изменения геймплея.', categories: ['Оптимизация', 'Сервер'] },
      { slug: 'ferritecore', title: 'FerriteCore', description: 'Снижает расход оперативной памяти.', categories: ['Оптимизация', 'Память'] },
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
  let requests = 0;

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
      server.middlewares.use(async (req, res, next) => {
        const url = (req.url ?? '').split('?')[0];
        if (!url.startsWith('/api/')) return next();
        const role = roleOf(req);

        if (url === '/api/auth/login' && req.method === 'POST') {
          const { login, password } = await readBody(req);
          const acc = accounts.find((a) => a.login === login && a.password === password);
          if (!acc) return send(res, 401, { detail: 'invalid' });
          const token = randomBytes(24).toString('hex');
          sessions.set(token, acc.role);
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
          await new Promise((r) => setTimeout(r, 1200));
          const q = query.trim().toLowerCase();
          if (q === '!ошибка') return send(res, 500, { detail: 'Не удалось выполнить поиск' });
          if (q === '!пусто') return send(res, 200, { mods: [], answer: null });
          const set = SETS[detectCostume(query).id];
          const mods = set.mods.map((m) => ({ ...m, url: `https://modrinth.com/mod/${m.slug}` }));
          return send(res, 200, { mods, answer: q === '!безответа' ? null : set.answer });
        }
        if (url === '/api/admin/stats' && req.method === 'GET') {
          if (!role) return send(res, 401, { detail: 'no session' });
          if (role !== 'admin') return send(res, 403, { detail: 'forbidden' });
          return send(res, 200, { requests });
        }
        return send(res, 404, { detail: 'not found' });
      });
    },
  };
}
